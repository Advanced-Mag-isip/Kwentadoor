from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Sum, Count
from expenses.models import Transaction
from analytics.services.chart import (
    get_income_utilization,
    get_payroll_vs_other_expenses,
    get_income_vs_expenses_vs_payroll,
    get_funding_runaway_projection,
    get_expenses_by_category,
    get_incoming_by_wallet,
)


def _get_qs(request):
    return Transaction.objects.all()


class IncomeUtilizationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = _get_qs(request)
        data = get_income_utilization(qs, year, period, month)
        return Response(data)


class PayrollVsOtherExpensesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = _get_qs(request)
        data = get_payroll_vs_other_expenses(qs, year, period, month)
        return Response(data)


class IncomeExpensesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = _get_qs(request)
        data = get_income_vs_expenses_vs_payroll(qs, year, period, month)
        return Response(data)


class FundingRunawayView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = _get_qs(request)
        data = get_funding_runaway_projection(qs, year, period, month)
        return Response(data)


class ExpensesByCategoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = _get_qs(request)
        data = get_expenses_by_category(qs, year, period, month)
        return Response(data)


class IncomingByWalletView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))
        qs = _get_qs(request)
        data = get_incoming_by_wallet(qs, year, month)
        return Response(data)


class MonthlyMetricsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        month = int(request.query_params.get("month", timezone.now().month))
        qs = _get_qs(request).filter(
            transaction_date__year=year,
            transaction_date__month=month,
        )
        incoming = qs.filter(transaction_type="add funds").aggregate(t=Sum("amount"))["t"] or 0
        outgoing = qs.filter(transaction_type="spend funds").aggregate(t=Sum("amount"))["t"] or 0
        count = qs.exclude(transaction_type="move funds").aggregate(c=Count("id"))["c"] or 0
        return Response({
            "incoming": round(float(incoming), 2),
            "outgoing": round(float(outgoing), 2),
            "profit": round(float(incoming) - float(outgoing), 2),
            "transaction_count": count,
        })