from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone

from payroll.models import (
    Worker,
    TimesheetSync,
    PayrollRun,
    PayrollEntry,
)
from .dtr_client import DTRClient


def _to_decimal(value, default=0):
    try:
        return Decimal(str(value or default)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal(str(default))


def sync_workers():
    client = DTRClient()
    dtr_workers = client.get_workers()
    
    # Get list of DTR worker IDs
    dtr_ids = [w['id'] for w in dtr_workers]
    
    # Delete workers that no longer exist in DTR
    deleted_count = Worker.objects.exclude(dtr_id__in=dtr_ids).delete()
    print(f"Deleted {deleted_count[0]} workers not in DTR")
    
    # Update or create remaining workers
    synced = []
    for w in dtr_workers:
        worker, created = Worker.objects.update_or_create(
            dtr_id=w['id'],
            defaults={
                'employee_id': w['employeeId'],
                'first_name': w['firstName'].strip(),
                'last_name': w['lastName'].strip(),
                'department': w.get('department') or '',
                'position': w.get('position') or '',
                'payment_type': w.get('paymentType', 'hourly'),
                'hourly_rate': _to_decimal(w.get('hourlyRate')),
                'daily_salary': _to_decimal(w.get('dailySalary')),
                'monthly_salary': _to_decimal(w.get('monthlySalary')),
                'overtime_hourly_rate': _to_decimal(w.get('overtimeHourlyRate')),
                'payment_method': w.get('paymentMethod', 'cash'),
                'is_active': True,
            }
        )
        synced.append(worker)

    return synced


def update_worker_rates(worker, data):
    """
    Updates worker rates in DTR first, then syncs local Worker table.
    data keys: hourly_rate, daily_salary, monthly_salary,
               overtime_hourly_rate, payment_type
    """
    client = DTRClient()

    # Map Django field names to DTR field names
    dtr_data = {}
    if 'hourly_rate' in data:
        dtr_data['hourlyRate'] = float(data['hourly_rate'])
    if 'daily_salary' in data:
        dtr_data['dailySalary'] = float(data['daily_salary'])
    if 'monthly_salary' in data:
        dtr_data['monthlySalary'] = float(data['monthly_salary'])
    if 'overtime_hourly_rate' in data:
        dtr_data['overtimeHourlyRate'] = float(data['overtime_hourly_rate'])
    if 'payment_type' in data:
        dtr_data['paymentType'] = data['payment_type']

    # Write to DTR first
    client.update_worker_rates(worker.dtr_id, dtr_data)

    # Then update local Worker table to stay in sync
    for field, value in data.items():
        setattr(worker, field, value)
    worker.save()

    return worker



def sync_timesheets(period_start, period_end):
    client = DTRClient()
    response = client.get_timesheet(period_start, period_end)
    shifts = response.get('data', [])

    # Remember which shift IDs were already paid before wiping
    already_paid_ids = set(
        TimesheetSync.objects.filter(
            period_start=period_start,
            period_end=period_end,
            is_paid_in_dtr=True
        ).values_list('dtr_shift_id', flat=True)
    )

    # Now wipe and re-sync
    TimesheetSync.objects.filter(
        period_start=period_start,
        period_end=period_end
    ).delete()

    created_syncs = []
    for row in shifts:
        try:
            worker = Worker.objects.get(dtr_id=row['workerId'])
        except Worker.DoesNotExist:
            continue

        shift_id = row.get('shiftId')
        # Prefer the DTR source-of-truth paid flag. Only fall back to the
        # previously stored local state when the DTR payload does not provide it.
        dtr_paid_flag = row.get('isPaid')
        if dtr_paid_flag is None:
            was_paid = shift_id in already_paid_ids if shift_id else False
        else:
            was_paid = bool(dtr_paid_flag)

        sync = TimesheetSync.objects.create(
            worker=worker,
            period_start=period_start,
            period_end=period_end,
            dtr_shift_id=row.get('shiftId'),
            date=row['date'],
            morning_time_in=row.get('morningTimeIn'),
            morning_time_out=row.get('morningTimeOut'),
            morning_hours=row.get('morningHours') or 0,
            afternoon_time_in=row.get('afternoonTimeIn'),
            afternoon_time_out=row.get('afternoonTimeOut'),
            afternoon_hours=row.get('afternoonHours') or 0,
            overtime_time_in=row.get('overtimeTimeIn'),
            overtime_time_out=row.get('overtimeTimeOut'),
            overtime_hours=row.get('overtimeHours') or 0,
            total_hours=row.get('totalHours') or 0,
            is_holiday=row.get('isHoliday', False),
            holiday_type=row.get('holidayType'),
            holiday_name=row.get('holidayName'),
            face_verified=row.get('faceVerified', False),
            is_paid_in_dtr=was_paid,  # ← preserve paid status
            paid_at_in_dtr=row.get('paidAt'),
        )
        created_syncs.append(sync)

    return created_syncs


def build_payroll_run(period_start, period_end, generated_by):
    """
    Gets gross pay from DTR's own salaryCalculator for each worker.
    Only includes unpaid shifts.
    """
    client = DTRClient()

    # Only workers with unpaid shifts in this period
    syncs = TimesheetSync.objects.filter(
        period_start=period_start,
        period_end=period_end,
        is_paid_in_dtr=False,
    ).select_related('worker')

    if not syncs.exists():
        raise ValueError(
            f"No unpaid timesheet data found for {period_start} to "
            f"{period_end}. Please sync timesheets first, or all shifts "
            "are already paid."
        )

    # Get unique workers with unpaid shifts
    workers_with_shifts = set(sync.worker.dtr_id for sync in syncs)

    # Delete existing draft for same period
    PayrollRun.objects.filter(
        period_start=period_start,
        period_end=period_end,
        status='draft'
    ).delete()

    payroll_run = PayrollRun.objects.create(
        period_start=period_start,
        period_end=period_end,
        status='draft',
        generated_by=generated_by,
    )

    entries = []
    total_gross = Decimal('0')

    for dtr_id in workers_with_shifts:
        worker = Worker.objects.get(dtr_id=dtr_id)

        try:
            # Use DTR's own salary calculator — no duplicate logic
            salary_data = client.get_salary(
                dtr_id=worker.dtr_id,
                start_date=period_start,
                end_date=period_end,
            )
        except Exception as e:
            print(f"Warning: Could not get salary for "
                  f"{worker.full_name}: {e}")
            continue

        gross = _to_decimal(salary_data.get('grossPay', 0))

        print("-------------")
        print(worker.full_name)
        print(salary_data)
        print("Gross:", gross)

        if gross == 0:
            continue

        entry = PayrollEntry.objects.create(
            payroll_run=payroll_run,
            worker=worker,
            total_working_hours=_to_decimal(
                salary_data.get('totalRegularHours', 0)
            ),
            total_overtime_hours=_to_decimal(
                salary_data.get('totalOvertimeHours', 0)
            ),
            total_days_worked=salary_data.get('daysWorked', 0),
            payment_type=worker.payment_type,
            hourly_rate=_to_decimal(salary_data.get('hourlyRate', 0)),
            overtime_hourly_rate=_to_decimal(
                salary_data.get('overtimeRate', 0)
            ),
            monthly_salary=worker.monthly_salary,
            gross_pay=gross,
            total_additions=Decimal('0'),
            total_deductions=Decimal('0'),
            net_pay=gross,
        )
        entries.append(entry)
        total_gross += gross

    payroll_run.total_gross_pay = total_gross
    payroll_run.total_net_pay = total_gross
    payroll_run.save()

    return payroll_run, entries


def recalculate_entry(entry):
    adjustments = entry.adjustments.all()

    total_additions = sum(
        a.amount for a in adjustments if a.type == 'addition'
    )
    total_deductions = sum(
        a.amount for a in adjustments if a.type == 'deduction'
    )

    entry.total_additions = _to_decimal(total_additions)
    entry.total_deductions = _to_decimal(total_deductions)
    entry.net_pay = (
        _to_decimal(entry.gross_pay)
        + entry.total_additions
        - entry.total_deductions
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    entry.save()

    run = entry.payroll_run
    all_entries = run.entries.all()
    run.total_gross_pay = sum(e.gross_pay for e in all_entries)
    run.total_deductions = sum(e.total_deductions for e in all_entries)
    run.total_net_pay = sum(e.net_pay for e in all_entries)
    run.save()

    return entry

def approve_payroll_run(payroll_run, source_wallet=None, wallet_id=None, user=None, shift_ids=None):
    """
    Finalizes payroll, creates transaction entries, and writes back to DTR.
    """
    payroll_run.status = 'approved'
    payroll_run.approved_at = timezone.now()
    if source_wallet:
        payroll_run.source_wallet = source_wallet
    payroll_run.save()

    # Create Transaction records in expenses app
    try:
        from expenses.models import Transaction, Wallet

        # Use the wallet_id passed directly if available
        wallet = None
        if wallet_id:
            try:
                wallet = Wallet.objects.get(id=wallet_id)
            except Wallet.DoesNotExist:
                print(f"WARNING: Wallet ID {wallet_id} not found")

        if wallet:
            for entry in payroll_run.entries.all():
                if entry.logged_to_expenses:
                    continue
                
                print(f"DEBUG: Creating transaction for {entry.worker.full_name}")
                print(f"DEBUG: gross_pay={entry.gross_pay}")
                print(f"DEBUG: total_additions={entry.total_additions}")
                print(f"DEBUG: total_deductions={entry.total_deductions}")
                print(f"DEBUG: net_pay={entry.net_pay}")

                Transaction.objects.create(
                    transaction_type='spend funds',
                    category='salaries',
                    transaction_date=payroll_run.period_end,
                    amount=entry.net_pay,
                    counterparty=entry.worker.full_name,
                    note=f"Payroll - {entry.worker.full_name} "
                         f"({payroll_run.period_start} to {payroll_run.period_end})",
                    wallet=wallet,
                    user=user or payroll_run.generated_by,
                )

            print(f"Transaction created for payroll run #{payroll_run.id}")
        else:
            print("WARNING: No wallet found, skipping transaction creation")

    except Exception as e:
        print(f"Could not log to expenses: {e}")
        import traceback
        traceback.print_exc()

    # Mark all entries as logged
    payroll_run.entries.update(logged_to_expenses=True)

    # Write back to DTR. Prefer the exact shift IDs from the pay action,
    # and fall back to the period-based lookup only when none were provided.
    if shift_ids is None:
        shift_ids = list(
            TimesheetSync.objects.filter(
                period_start=payroll_run.period_start,
                period_end=payroll_run.period_end,
                is_paid_in_dtr=False,
            ).exclude(dtr_shift_id__isnull=True)
            .values_list('dtr_shift_id', flat=True)
        )
    else:
        shift_ids = [shift_id for shift_id in shift_ids if shift_id is not None]

    print(f"DEBUG shift_ids to mark paid: {shift_ids}")

    if shift_ids:
        try:
            client = DTRClient()
            client.mark_paid(shift_ids)

            TimesheetSync.objects.filter(
                dtr_shift_id__in=shift_ids
            ).update(
                is_paid_in_dtr=True,
                paid_at_in_dtr=timezone.now()
            )
            print(f"Marked {len(shift_ids)} shifts as paid in DTR")
        except Exception as e:
            print(f"WARNING DTR write-back failed: {e}")

    return payroll_run