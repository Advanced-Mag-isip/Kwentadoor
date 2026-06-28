from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Worker, TimesheetSync, PayrollRun, PayrollEntry, PayrollAdjustment
from .serializers import (
    WorkerSerializer,
    TimesheetSyncSerializer,
    PayrollRunSerializer,
    PayrollRunListSerializer,
    PayrollEntrySerializer,
    PayrollAdjustmentSerializer,
)
from .services.payroll_calculator import (
    sync_workers,
    sync_timesheets,
    build_payroll_run,
    recalculate_entry,
    approve_payroll_run,
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_workers_view(request):
    """
    POST /api/payroll/workers/sync/
    Pulls all active workers from DTR and upserts into local Worker table.
    """
    try:
        workers = sync_workers()
        return Response({
            'status': 'synced',
            'count': len(workers)
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_workers(request):
    """
    GET /api/payroll/workers/
    Returns all workers in the local Worker table.
    """
    workers = Worker.objects.filter(is_active=True).order_by('last_name')
    serializer = WorkerSerializer(workers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_timesheets_view(request):
    """
    POST /api/payroll/timesheets/sync/
    Body: { period_start, period_end }
    Pulls raw timesheet data from DTR for the given period.
    This is Step 1 — no money calculated yet.
    """
    period_start = request.data.get('period_start')
    period_end = request.data.get('period_end')

    if not period_start or not period_end:
        return Response(
            {'error': 'period_start and period_end are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        syncs = sync_timesheets(period_start, period_end)
        return Response({
            'status': 'synced',
            'period_start': period_start,
            'period_end': period_end,
            'records_synced': len(syncs),
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_timesheets(request):
    """
    GET /api/payroll/timesheets/?period_start=&period_end=&worker_id=
    Returns synced timesheet records, optionally filtered.
    """
    period_start = request.query_params.get('period_start')
    period_end = request.query_params.get('period_end')
    worker_id = request.query_params.get('worker_id')

    syncs = TimesheetSync.objects.select_related('worker').all()

    if period_start:
        syncs = syncs.filter(period_start=period_start)
    if period_end:
        syncs = syncs.filter(period_end=period_end)
    if worker_id:
        syncs = syncs.filter(worker__id=worker_id)

    syncs = syncs.order_by('worker__last_name', 'date')
    serializer = TimesheetSyncSerializer(syncs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payroll_runs(request):
    """
    GET /api/payroll/runs/
    Returns all payroll runs — lightweight list view.
    Supports filter by status: ?status=draft or ?status=approved
    """
    runs = PayrollRun.objects.all().order_by('-generated_at')

    run_status = request.query_params.get('status')
    if run_status:
        runs = runs.filter(status=run_status)

    serializer = PayrollRunListSerializer(runs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payroll_run(request, pk):
    """
    GET /api/payroll/runs/<id>/
    Returns a single payroll run with all entries and adjustments.
    This is the Review Payroll screen data.
    """
    run = get_object_or_404(PayrollRun, pk=pk)
    serializer = PayrollRunSerializer(run)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def build_payroll_run_view(request):
    """
    POST /api/payroll/runs/build/
    Body: { period_start, period_end }
    Builds a draft payroll run from synced timesheets.
    This is Step 2 — calculates gross pay per worker.
    """
    period_start = request.data.get('period_start')
    period_end = request.data.get('period_end')

    if not period_start or not period_end:
        return Response(
            {'error': 'period_start and period_end are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        payroll_run, entries = build_payroll_run(
            period_start,
            period_end,
            generated_by=request.user,
        )
        serializer = PayrollRunSerializer(payroll_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_payroll_run_view(request, pk):
    """
    POST /api/payroll/runs/<id>/approve/
    Body: { source_wallet }
    Finalizes the payroll run and logs to expenses.
    This is the 'Approve & Log to Expenses' button.
    """
    run = get_object_or_404(PayrollRun, pk=pk)

    if run.status == 'approved':
        return Response(
            {'error': 'This payroll run has already been approved'},
            status=status.HTTP_400_BAD_REQUEST
        )

    source_wallet = request.data.get('source_wallet')
    run = approve_payroll_run(run, source_wallet=source_wallet)
    serializer = PayrollRunSerializer(run)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payroll_entry(request, pk):
    """
    GET /api/payroll/entries/<id>/
    Returns a single payroll entry with adjustments.
    This is the View Payroll Information modal data.
    """
    entry = get_object_or_404(
        PayrollEntry.objects.select_related('worker', 'payroll_run'),
        pk=pk
    )
    serializer = PayrollEntrySerializer(entry)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_adjustment(request, entry_id):
    """
    POST /api/payroll/entries/<entry_id>/adjustments/
    Body: { type, category, amount, reason }
    Adds a bonus or deduction to a payroll entry.
    This is the 'Add Adjustment' modal.
    """
    entry = get_object_or_404(PayrollEntry, pk=entry_id)

    if entry.payroll_run.status == 'approved':
        return Response(
            {'error': 'Cannot adjust an approved payroll run'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = PayrollAdjustmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(payroll_entry=entry)
        recalculate_entry(entry)
        updated_entry = PayrollEntrySerializer(entry)
        return Response(updated_entry.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_adjustment(request, entry_id, adjustment_id):
    """
    DELETE /api/payroll/entries/<entry_id>/adjustments/<adjustment_id>/
    Removes an adjustment and recalculates net pay.
    """
    entry = get_object_or_404(PayrollEntry, pk=entry_id)

    if entry.payroll_run.status == 'approved':
        return Response(
            {'error': 'Cannot adjust an approved payroll run'},
            status=status.HTTP_400_BAD_REQUEST
        )

    adjustment = get_object_or_404(PayrollAdjustment, pk=adjustment_id, payroll_entry=entry)
    adjustment.delete()
    recalculate_entry(entry)
    updated_entry = PayrollEntrySerializer(entry)
    return Response(updated_entry.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_worker_rates_view(request, pk):
    """
    PUT /api/payroll/workers/<id>/rates/
    Updates worker rates in DTR and syncs local Worker table.
    """
    worker = get_object_or_404(Worker, pk=pk)

    allowed_fields = [
        'hourly_rate',
        'daily_salary',
        'monthly_salary',
        'overtime_hourly_rate',
        'payment_type',
    ]

    data = {
        k: v for k, v in request.data.items()
        if k in allowed_fields
    }

    if not data:
        return Response(
            {'error': 'No valid fields provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .services.payroll_calculator import update_worker_rates
        worker = update_worker_rates(worker, data)
        serializer = WorkerSerializer(worker)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )