from django.urls import path
from .views.summary import TransactionSummaryView
from .views.endpoints import endpoints_view, available_periods
from .views.chart import (
    IncomeExpensesView,
    FundingRunawayView,
    ExpensesByCategoryView,
    PayrollVsOtherExpensesView,
    IncomeUtilizationView,
)

urlpatterns = [
    path("summary/", TransactionSummaryView.as_view(), name="transaction-summary"),
    path("endpoints/", endpoints_view, name="endpoints"),
    path("available-periods/", available_periods, name="available-periods"),
    path("charts/income-vs-expenses/", IncomeExpensesView.as_view(), name="income-vs-expenses"),
    path("charts/funding-runaway-projection/", FundingRunawayView.as_view(), name="funding-runaway-projection"),
    path("charts/expenses-by-category/", ExpensesByCategoryView.as_view(), name="expenses-by-category"),
    path("charts/payroll-vs-other/", PayrollVsOtherExpensesView.as_view(), name="payroll-vs-other"),
    path("charts/income-utilization/", IncomeUtilizationView.as_view(), name="income-utilization"),
]