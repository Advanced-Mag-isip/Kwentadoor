from django.shortcuts import render
from expenses.models import Transaction


ENDPOINTS = [
    {
        "method": "GET",
        "path": "/api/analytics/summary/",
        "description": "Return aggregated income and expense totals for a given period.",
        "params": [
            {"name": "period", "type": "string", "default": "monthly", "desc": "One of: monthly, quarterly, yearly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Filter year (e.g. 2026)"},
            {"name": "month", "type": "int", "default": "current", "desc": "Filter month 1-12"},
        ],
        "fields": [
            {"name": "total_income", "type": "float", "desc": "Sum of all income"},
            {"name": "total_expenses", "type": "float", "desc": "Sum of all expenses"},
            {"name": "average_income", "type": "float", "desc": "Average income per transaction"},
            {"name": "average_expenses", "type": "float", "desc": "Average expense per transaction"},
            {"name": "expense_growth", "type": "float|null", "desc": "% change vs previous period"},
            {"name": "missing_receipt_count", "type": "int", "desc": "Expenses without attachments"},
            {"name": "undocumented_expenses_pct", "type": "float", "desc": "% of expenses missing receipts"},
            {"name": "runaway", "type": "string", "desc": "Runway duration (e.g. '5 months', '114 days')"},
        ],
    },
    {
        "method": "GET",
        "path": "/api/analytics/charts/income-vs-expenses/",
        "description": "Income vs expenses breakdown — yearly=Jan-Dec, quarterly=Q1-Q4, monthly=W1-W5.",
        "params": [
            {"name": "period", "type": "string", "default": "yearly", "desc": "yearly, quarterly, or monthly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Filter year (e.g. 2026)"},
            {"name": "month", "type": "int", "desc": "Required if period=monthly (1-12)"},
        ],
        "fields": [
            {"name": "income", "type": "object", "desc": "{Jan/Month: 0, ...} or {Q1: 0, ...} or {W1: 0, ...}"},
            {"name": "expenses", "type": "object", "desc": "{Jan/Month: 0, ...} or {Q1: 0, ...} or {W1: 0, ...}"},
        ],
    },
    {
        "method": "GET",
        "path": "/api/analytics/charts/funding-runaway-projection/",
        "description": "Simple runway-style view — how long current balance could cover average monthly expenses.",
        "params": [
            {"name": "period", "type": "string", "default": "yearly", "desc": "yearly, quarterly, or monthly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Projection year (e.g. 2026)"},
            {"name": "month", "type": "int", "desc": "Required if period=monthly (1-12)"},
        ],
        "fields": [
            {"name": "current_balance", "type": "float", "desc": "Total income minus total expenses (all-time)"},
            {"name": "avg_monthly_expenses", "type": "float", "desc": "Average monthly expenses for the selected period"},
            {"name": "runway_months", "type": "float", "desc": "Months until balance is depleted"},
            {"name": "runway_display", "type": "string", "desc": "Human-readable runway duration"},
            {"name": "chart", "type": "object", "desc": "{labels: [monthly labels], values: [projected balances]}"},
        ],
    },
    {
        "method": "GET",
        "path": "/api/analytics/charts/expenses-by-category/",
        "description": "Expenses grouped by category — yearly=Jan-Dec, quarterly=Q1-Q4, monthly=W1-W5.",
        "params": [
            {"name": "period", "type": "string", "default": "yearly", "desc": "yearly, quarterly, or monthly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Filter year (e.g. 2026)"},
            {"name": "month", "type": "int", "desc": "Required if period=monthly (1-12)"},
        ],
        "fields": [
            {"name": "<period_key>", "type": "object", "desc": "Key is Jan/Q1/W1, value is {category: {amount, percentage}}"},
        ],
    },
    {
        "method": "GET",
        "path": "/api/analytics/charts/payroll-vs-other/",
        "description": "Payroll vs other expenses — yearly=Jan-Dec, quarterly=Q1-Q4, monthly=W1-W5.",
        "params": [
            {"name": "period", "type": "string", "default": "yearly", "desc": "yearly, quarterly, or monthly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Filter year (e.g. 2026)"},
            {"name": "month", "type": "int", "desc": "Required if period=monthly (1-12)"},
        ],
        "fields": [
            {"name": "payroll_vs_other", "type": "object", "desc": "{period_key: {payroll, other_expenses}}"},
        ],
    },
    {
        "method": "GET",
        "path": "/api/analytics/charts/income-utilization/",
        "description": "Income vs expenses vs balance — yearly=Jan-Dec, quarterly=Q1-Q4, monthly=W1-W5.",
        "params": [
            {"name": "period", "type": "string", "default": "yearly", "desc": "yearly, quarterly, or monthly"},
            {"name": "year", "type": "int", "default": "current", "desc": "Filter year (e.g. 2026)"},
            {"name": "month", "type": "int", "desc": "Required if period=monthly (1-12)"},
        ],
        "fields": [
            {"name": "income_utilization", "type": "object", "desc": "{period_key: {income, expenses, balance}}"},
        ],
    },
]


def endpoints_view(request):
    years = Transaction.objects.dates("transaction_date", "year", order="ASC")
    year_list = [d.year for d in years]
    return render(request, "analytics/endpoints.html", {
        "endpoints": ENDPOINTS,
        "available_years": year_list,
    })
