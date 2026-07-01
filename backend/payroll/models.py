from django.db import models
from django.conf import settings


class Worker(models.Model):
    """
    Mirrors DTR employee data.
    Synced from DTR, not the source of truth.
    """
    dtr_id = models.IntegerField(unique=True)           
    employee_id = models.CharField(max_length=50)       
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)

    PAYMENT_TYPE_CHOICES = [
        ('hourly', 'Hourly'),
        ('monthly', 'Monthly'),
    ]
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        default='hourly'
    )

    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TimesheetSync(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='timesheet_syncs')
    period_start = models.DateField()
    period_end = models.DateField()
    synced_at = models.DateTimeField(auto_now_add=True)

    dtr_shift_id = models.IntegerField(null=True, blank=True)

    date = models.DateField()
    morning_time_in = models.CharField(max_length=10, blank=True, null=True)
    morning_time_out = models.CharField(max_length=10, blank=True, null=True)
    morning_hours = models.FloatField(default=0)
    afternoon_time_in = models.CharField(max_length=10, blank=True, null=True)
    afternoon_time_out = models.CharField(max_length=10, blank=True, null=True)
    afternoon_hours = models.FloatField(default=0)
    overtime_time_in = models.CharField(max_length=10, blank=True, null=True)
    overtime_time_out = models.CharField(max_length=10, blank=True, null=True)
    overtime_hours = models.FloatField(default=0)
    total_hours = models.FloatField(default=0)

    is_holiday = models.BooleanField(default=False)
    holiday_type = models.CharField(max_length=30, choices=[
        ('regular', 'Regular Holiday'),
        ('special_non_working', 'Special Non-Working'),
        ('special_working', 'Special Working'),
    ], blank=True, null=True)
    holiday_name = models.CharField(max_length=100, blank=True, null=True)
    face_verified = models.BooleanField(default=False)

    is_paid_in_dtr = models.BooleanField(default=False)
    paid_at_in_dtr = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.worker.full_name} - {self.date}"


class PayrollRun(models.Model):
    """
    One payroll generation event for a date range.
    Created when admin clicks 'Approve & Log to Expenses'.
    """
    period_start = models.DateField()
    period_end = models.DateField()

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    total_gross_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    source_wallet = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    generated_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payroll_runs'
    )

    def __str__(self):
        return f"Payroll {self.period_start} to {self.period_end} [{self.status}]"


class PayrollEntry(models.Model):
    """
    One worker's pay calculation within a payroll run.
    Shown in the Review Payroll screen.
    """
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    payroll_run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)

    # Hours summary — from TimesheetSync
    total_working_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_days_worked = models.IntegerField(default=0)
    total_absences = models.IntegerField(default=0)

    # Rate snapshot — copied from Worker at time of payroll run
    payment_type = models.CharField(max_length=10)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Auto-calculated
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # From Add Adjustment modal
    total_additions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Final
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Tracks if this entry has been logged to expenses app
    logged_to_expenses = models.BooleanField(default=False)

    # ADD THIS FIELD
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )

    def __str__(self):
        return f"{self.worker.full_name} - {self.payroll_run}"


class PayrollAdjustment(models.Model):
    """
    Manual bonus or deduction per employee per payroll run.
    Created via the 'Add Adjustment' modal.
    """
    payroll_entry = models.ForeignKey(
        PayrollEntry,
        on_delete=models.CASCADE,
        related_name='adjustments'
    )

    TYPE_CHOICES = [
        ('addition', 'Addition'),
        ('deduction', 'Deduction'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    CATEGORY_CHOICES = [
        ('bonus', 'Bonus'),
        ('cash_advance', 'Cash Advance Repayment'),
        ('overtime_premium', 'Overtime Premium'),
        ('allowance', 'Allowance'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount}"