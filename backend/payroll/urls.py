from django.urls import path
from . import views

urlpatterns = [
    # Workers
    path('workers/', views.list_workers),
    path('workers/sync/', views.sync_workers_view),

    # Timesheets
    path('timesheets/', views.list_timesheets),
    path('timesheets/sync/', views.sync_timesheets_view),

    # Payroll Runs
    path('runs/', views.list_payroll_runs),
    path('runs/build/', views.build_payroll_run_view),
    path('runs/<int:pk>/', views.get_payroll_run),
    path('runs/<int:pk>/approve/', views.approve_payroll_run_view),

    # Entries
    path('entries/<int:pk>/', views.get_payroll_entry),

    # Adjustments
    path('entries/<int:entry_id>/adjustments/', views.add_adjustment),
    path('entries/<int:entry_id>/adjustments/<int:adjustment_id>/', views.delete_adjustment),
    path('employees/<int:employee_id>/pay/', views.pay_employee, name='pay_employee'),

    path('workers/<int:pk>/rates/', views.update_worker_rates_view),

    path('summary/', views.payroll_summary, name='payroll_summary'),
    
    path('employees/', views.employee_payroll_list, name='employee_payroll_list'),

    path('workers/status/', views.workers_payment_status, name='workers_status'),

    path('export/xlsx/', views.export_payroll_xlsx, name='export_payroll_xlsx'),

]