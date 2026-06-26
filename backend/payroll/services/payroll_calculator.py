from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone

from payroll.models import (
    Worker,
    TimesheetSync,
    PayrollRun,
    PayrollEntry,
)
from .dtr_client import DTRClient

def sync_workers():
    """
    Pull all active workers from DTR and upsert into local Worker table.
    Called manually or before every payroll run.
    """
    client = DTRClient()
    dtr_workers = client.get_workers()

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
                'hourly_rate': Decimal(str(w.get('hourlyRate') or 0)),
                'daily_salary': Decimal(str(w.get('dailySalary') or 0)),
                'monthly_salary': Decimal(str(w.get('monthlySalary') or 0)),
                'overtime_hourly_rate': Decimal(str(w.get('overtimeHourlyRate') or 0)),
                'payment_method': w.get('paymentMethod', 'cash'),
                'is_active': True,
            }
        )
        synced.append(worker)

    return synced


def sync_timesheets(period_start, period_end):
    """
    Pull timesheet data from DTR for a date range and store as
    TimesheetSync records. This is the 'Sync Timesheets' step —
    raw hours only, no pay calculation yet.
    """
    client = DTRClient()
    response = client.get_timesheet(period_start, period_end)
    shifts = response.get('data', [])

    # Clear existing syncs for this period to avoid duplicates on re-sync
    TimesheetSync.objects.filter(
        period_start=period_start,
        period_end=period_end
    ).delete()

    created_syncs = []
    for row in shifts:
        try:
            worker = Worker.objects.get(dtr_id=row['workerId'])
        except Worker.DoesNotExist:
            # Worker not synced yet — skip
            continue

        sync = TimesheetSync.objects.create(
            worker=worker,
            period_start=period_start,
            period_end=period_end,
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
        )
        created_syncs.append(sync)

    return created_syncs


def _to_decimal(value, default=0):
    """Safely convert any value to Decimal."""
    try:
        return Decimal(str(value or default)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal(str(default))


def _calculate_gross(worker, total_working_hours, total_overtime_hours, total_days_worked):
    """
    Calculate gross pay based on payment type.

    Hourly:  gross = (regular_hours x hourly_rate) + (overtime_hours x overtime_rate)
    Monthly: gross = monthly_salary (fixed) + overtime premium if any
    """
    regular_hours = total_working_hours - total_overtime_hours

    if worker.payment_type == 'hourly':
        hourly_rate = _to_decimal(worker.hourly_rate)

        # Fall back to daily_salary / 8 if hourly_rate is 0
        if hourly_rate == 0 and worker.daily_salary > 0:
            hourly_rate = _to_decimal(worker.daily_salary) / 8

        overtime_rate = _to_decimal(worker.overtime_hourly_rate)

        # If no overtime rate set, default to 1.25x hourly rate
        if overtime_rate == 0:
            overtime_rate = hourly_rate * Decimal('1.25')

        gross = (regular_hours * hourly_rate) + (total_overtime_hours * overtime_rate)

    else:
        # Monthly — fixed salary + overtime premium
        monthly_salary = _to_decimal(worker.monthly_salary)
        overtime_rate = _to_decimal(worker.overtime_hourly_rate)

        if overtime_rate == 0:
            # Derive hourly from monthly: monthly / 22 working days / 8 hours
            overtime_rate = (monthly_salary / 22 / 8) * Decimal('1.25')

        overtime_premium = total_overtime_hours * overtime_rate
        gross = monthly_salary + overtime_premium

    return gross.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def build_payroll_run(period_start, period_end, generated_by):
    """
    Read synced TimesheetSync records for the period and create a
    draft PayrollRun with one PayrollEntry per worker.
    Does NOT approve or log to expenses yet.
    """
    syncs = TimesheetSync.objects.filter(
        period_start=period_start,
        period_end=period_end
    ).select_related('worker')

    if not syncs.exists():
        raise ValueError(
            f"No timesheet data found for {period_start} to {period_end}. "
            "Please sync timesheets first."
        )

    # Group syncs by worker
    worker_data = {}
    for sync in syncs:
        wid = sync.worker.dtr_id
        if wid not in worker_data:
            worker_data[wid] = {
                'worker': sync.worker,
                'total_working_hours': Decimal('0'),
                'total_overtime_hours': Decimal('0'),
                'total_days_worked': 0,
            }

        worker_data[wid]['total_working_hours'] += _to_decimal(sync.total_hours)
        worker_data[wid]['total_overtime_hours'] += _to_decimal(sync.overtime_hours)

        if sync.total_hours and sync.total_hours > 0:
            worker_data[wid]['total_days_worked'] += 1

    # Create draft PayrollRun
    payroll_run = PayrollRun.objects.create(
        period_start=period_start,
        period_end=period_end,
        status='draft',
        generated_by=generated_by,
    )

    entries = []
    total_gross = Decimal('0')

    for wid, data in worker_data.items():
        worker = data['worker']
        total_working_hours = data['total_working_hours']
        total_overtime_hours = data['total_overtime_hours']
        total_days_worked = data['total_days_worked']

        gross = _calculate_gross(
            worker,
            total_working_hours,
            total_overtime_hours,
            total_days_worked
        )

        entry = PayrollEntry.objects.create(
            payroll_run=payroll_run,
            worker=worker,
            total_working_hours=total_working_hours,
            total_overtime_hours=total_overtime_hours,
            total_days_worked=total_days_worked,
            payment_type=worker.payment_type,
            hourly_rate=worker.hourly_rate,
            overtime_hourly_rate=worker.overtime_hourly_rate,
            monthly_salary=worker.monthly_salary,
            gross_pay=gross,
            total_additions=Decimal('0'),
            total_deductions=Decimal('0'),
            net_pay=gross,
        )
        entries.append(entry)
        total_gross += gross

    # Update run totals
    payroll_run.total_gross_pay = total_gross
    payroll_run.total_net_pay = total_gross
    payroll_run.save()

    return payroll_run, entries


def recalculate_entry(entry):
    """
    Called after an adjustment is added or removed.
    Recalculates total_additions, total_deductions, and net_pay
    for a single PayrollEntry.
    """
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

    # Update run totals
    run = entry.payroll_run
    all_entries = run.entries.all()
    run.total_gross_pay = sum(e.gross_pay for e in all_entries)
    run.total_deductions = sum(e.total_deductions for e in all_entries)
    run.total_net_pay = sum(e.net_pay for e in all_entries)
    run.save()

    return entry


def approve_payroll_run(payroll_run, source_wallet=None):
    """
    Finalizes the payroll run.
    Sets status to approved and records the timestamp.
    The expenses logging happens separately in the expenses app.
    """
    payroll_run.status = 'approved'
    payroll_run.approved_at = timezone.now()

    if source_wallet:
        payroll_run.source_wallet = source_wallet

    payroll_run.save()

    # Mark all entries as logged
    payroll_run.entries.update(logged_to_expenses=True)

    return payroll_run