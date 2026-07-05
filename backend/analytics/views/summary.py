from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from expenses.models import Transaction
from analytics.models import TransactionsAuditLog as AuditLog
from analytics.services.summary import (
    get_monthly_summary,
    get_quarterly_summary,
    get_yearly_summary,
)
from analytics.services.export import export_transactions_to_xlsx, export_summary_to_pdf

# 1. Separate the Queryset Fetchers
def _get_transaction_qs(request):
    """Fetches the base queryset for financial summaries."""
    if request.user.is_authenticated:
        return Transaction.objects.filter(user=request.user)
    return Transaction.objects.all()

def _get_auditlog_qs(request):
    """Fetches the base queryset for raw audit exports."""
    if request.user.is_authenticated:
        return AuditLog.objects.filter(user=request.user)
    return AuditLog.objects.all()


class TransactionSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        # Drive summaries entirely off the Transaction model
        qs = _get_transaction_qs(request)

        if period == "yearly":
            data = get_yearly_summary(qs, year)
        elif period == "quarterly":
            data = get_quarterly_summary(qs, year, month)
        else:
            data = get_monthly_summary(qs, year, month)

        return Response(data)


class DataExportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))
        export_format = request.query_params.get("export_format", "xlsx") 

        # 2. Fetch both datasets simultaneously
        transaction_qs = _get_transaction_qs(request)
        audit_qs = _get_auditlog_qs(request)

        # 3. Filter AuditLogs (using `timestamp`) and calculate Summaries (using `transaction_qs`)
        if period == "yearly":
            filtered_audit_qs = audit_qs.filter(transaction_date__year=year)
            summary_data = get_yearly_summary(transaction_qs, year)[-1] if get_yearly_summary(transaction_qs, year) else {}
            period_label = f"Year_{year}"
            
        elif period == "quarterly":
            q_start = ((month - 1) // 3) * 3 + 1
            q_end = q_start + 2
            filtered_audit_qs = audit_qs.filter(
                transaction_date__year=year, 
                transaction_date__month__gte=q_start, 
                transaction_date__month__lte=q_end
            )
            summary_data = get_quarterly_summary(transaction_qs, year, month)
            period_label = f"Q{(month-1)//3 + 1}_{year}"
            
        else: # monthly
            filtered_audit_qs = audit_qs.filter(transaction_date__year=year, transaction_date__month=month)
            summary_data = get_monthly_summary(transaction_qs, year, month)
            period_label = f"Month_{month}_{year}"

        # 4. Route the decoupled data to your export services
        if export_format == "xlsx":
            # You may want to rename 'export_transactions_to_xlsx' to 'export_auditlogs_to_xlsx' internally
            return export_transactions_to_xlsx(filtered_audit_qs, period_label)
            
        elif export_format == "pdf":
            # Provide the PDF service with both the math (summary_data) and the raw lists (filtered_audit_qs)
            return export_summary_to_pdf(summary_data, filtered_audit_qs, period_label)