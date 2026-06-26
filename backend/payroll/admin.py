from django.contrib import admin
from .models import Worker, TimesheetSync, PayrollRun, PayrollEntry, PayrollAdjustment

admin.site.register(Worker)
admin.site.register(TimesheetSync)
admin.site.register(PayrollRun)
admin.site.register(PayrollEntry)
admin.site.register(PayrollAdjustment)