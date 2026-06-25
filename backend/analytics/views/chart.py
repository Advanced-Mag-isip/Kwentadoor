from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from expenses.models import Transaction
from analytics.services.chart import (
    get_income_utilization,
    get_payroll_vs_other_expenses,
    get_income_vs_expenses_vs_payroll,
    get_funding_runaway_projection,
    get_expenses_by_category,
)


class IncomeUtilizationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = Transaction.objects.filter(user=request.user)
        data = get_income_utilization(qs, year, period, month)
        return Response(data)


class PayrollVsOtherExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = Transaction.objects.filter(user=request.user)
        data = get_payroll_vs_other_expenses(qs, year, period, month)
        return Response(data)


class IncomeExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = Transaction.objects.filter(user=request.user)
        data = get_income_vs_expenses_vs_payroll(qs, year, period, month)
        return Response(data)


class FundingRunawayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = Transaction.objects.filter(user=request.user)
        data = get_funding_runaway_projection(qs, year, period, month)
        return Response(data)


class ExpensesByCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", timezone.now().year))
        period = request.query_params.get("period", "yearly")
        month = request.query_params.get("month")
        qs = Transaction.objects.filter(user=request.user)
        data = get_expenses_by_category(qs, year, period, month)
        return Response(data)
