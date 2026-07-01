from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from expenses.models import Transaction
from analytics.services.summary import (
    get_monthly_summary,
    get_quarterly_summary,
    get_yearly_summary,
)


def _get_qs(request):
    if request.user.is_authenticated:
        return Transaction.objects.filter(user=request.user)
    return Transaction.objects.all()


class TransactionSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))

        qs = _get_qs(request)

        if period == "yearly":
            data = get_yearly_summary(qs, year)
        elif period == "quarterly":
            data = get_quarterly_summary(qs, year, month)
        else:
            data = get_monthly_summary(qs, year, month)

        return Response(data)


from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .summary import _get_qs, get_monthly_summary, get_quarterly_summary, get_yearly_summary
from analytics.services.export import export_transactions_to_xlsx, export_summary_to_pdf

class DataExportView(APIView):
    permission_classes = [AllowAny] # Match your summary view permissions

    def get(self, request):

        print("==== EXPORT VIEW WAS TRIGGERED! ====")

        period = request.query_params.get("period", "monthly")
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))
        export_format = request.query_params.get("export_format", "xlsx") 

        qs = _get_qs(request)

        # Apply date filtering to the base queryset based on period
        if period == "yearly":
            filtered_qs = qs.filter(transaction_date__year=year)
            summary_data = get_yearly_summary(qs, year)[-1] if get_yearly_summary(qs, year) else {}
            period_label = f"Year_{year}"
        elif period == "quarterly":
            q_start = ((month - 1) // 3) * 3 + 1
            q_end = q_start + 2
            filtered_qs = qs.filter(transaction_date__year=year, transaction_date__month__gte=q_start, transaction_date__month__lte=q_end)
            summary_data = get_quarterly_summary(qs, year, month)
            period_label = f"Q{(month-1)//3 + 1}_{year}"
        else:
            filtered_qs = qs.filter(transaction_date__year=year, transaction_date__month=month)
            summary_data = get_monthly_summary(qs, year, month)
            period_label = f"Month_{month}_{year}"

        if export_format == "xlsx":
            return export_transactions_to_xlsx(filtered_qs)
        elif export_format == "pdf":
            return export_summary_to_pdf(summary_data, filtered_qs, period_label)