from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum
from django.utils.dateparse import parse_date

from .models import Wallet, Transaction, Attachment, Log
from .serializers import WalletSerializer, TransactionSerializer, AttachmentSerializer, LogSerializer
from .constants import EXPENSE_CATEGORIES_DATA

# Pagination class to improve performance on large datasets
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class CategoryViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing static expense categories.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(EXPENSE_CATEGORIES_DATA)

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)

        Log.objects.create(
            user=self.request.user,
            action="Create Expense",
            new_data=serializer.data
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_data = self.get_serializer(instance).data
        
        transaction = serializer.save()
        
        Log.objects.create(
            user=self.request.user,
            action="Update Expense",
            old_data=old_data,
            new_data=serializer.data
        )

    def perform_destroy(self, instance):
        old_data = self.get_serializer(instance).data
        
        Log.objects.create(
            user=self.request.user,
            action="Delete Expense",
            old_data=old_data
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Calculates key metrics for the dashboard (Income, Expenses, Net Balance).
        """
        transactions = self.get_queryset()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                transactions = transactions.filter(transaction_date__gte=parsed_start)
                
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                transactions = transactions.filter(transaction_date__lte=parsed_end)
        
        expenses = transactions.filter(transaction_type='spend funds')
        income = transactions.filter(transaction_type='add funds')

        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
        total_income = income.aggregate(Sum('amount'))['amount__sum'] or 0.0
        net_balance = total_income - total_expenses

        expenses_by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        
        return Response({
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "expenses_by_category": list(expenses_by_category)
        })

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination