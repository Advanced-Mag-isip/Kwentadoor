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
