from rest_framework import serializers
from .models import Worker, TimesheetSync, PayrollRun, PayrollEntry, PayrollAdjustment


class WorkerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Worker
        fields = '__all__'


class TimesheetSyncSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.full_name', read_only=True)
    worker_employee_id = serializers.CharField(source='worker.employee_id', read_only=True)

    class Meta:
        model = TimesheetSync
        fields = '__all__'


class PayrollAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAdjustment
        fields = '__all__'


class PayrollEntrySerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.full_name', read_only=True)
    worker_employee_id = serializers.CharField(source='worker.employee_id', read_only=True)
    worker_position = serializers.CharField(source='worker.position', read_only=True)
    worker_department = serializers.CharField(source='worker.department', read_only=True)
    worker_payment_method = serializers.CharField(source='worker.payment_method', read_only=True)
    adjustments = PayrollAdjustmentSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollEntry
        fields = '__all__'


class PayrollRunSerializer(serializers.ModelSerializer):
    entries = PayrollEntrySerializer(many=True, read_only=True)
    generated_by_username = serializers.CharField(
        source='generated_by.username',
        read_only=True
    )

    class Meta:
        model = PayrollRun
        fields = '__all__'


class PayrollRunListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the payroll list view.
    Does not nest entries — just the run summary.
    """
    generated_by_username = serializers.CharField(
        source='generated_by.username',
        read_only=True
    )
    entry_count = serializers.IntegerField(
        source='entries.count',
        read_only=True
    )

    class Meta:
        model = PayrollRun
        fields = [
            'id',
            'period_start',
            'period_end',
            'status',
            'total_gross_pay',
            'total_deductions',
            'total_net_pay',
            'source_wallet',
            'generated_at',
            'approved_at',
            'generated_by_username',
            'entry_count',
        ]