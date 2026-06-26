from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils.dateparse import parse_date

from .models import Wallet, Transaction, Attachment, Log
from .serializers import WalletSerializer, TransactionSerializer, AttachmentSerializer, LogSerializer
from .constants import EXPENSE_CATEGORIES_DATA

class CategoryViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing static expense categories.
    Accessed via /api/expenses/categories/
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(EXPENSE_CATEGORIES_DATA)

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)

        Log.objects.create(
            user=self.request.user,
            action="Create Expense",
            new_data=serializer.data
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        # Serialize the old data safely before updating
        old_data = self.get_serializer(instance).data
        
        transaction = serializer.save()
        
        Log.objects.create(
            user=self.request.user,
            action="Update Expense",
            old_data=old_data,
            new_data=serializer.data
        )

    def perform_destroy(self, instance):
        # Serialize before destroying
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
        Simple analytics module returning key metrics for the dashboard.
        Supports filtering via `start_date` and `end_date` query params.
        """

        expenses = self.get_queryset().filter(transaction_type='spend funds')
        
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                expenses = expenses.filter(transaction_date__gte=parsed_start)
                
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                expenses = expenses.filter(transaction_date__lte=parsed_end)
        
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
        expenses_by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        
        return Response({
            "total_expenses": total_expenses,
            "expenses_by_category": list(expenses_by_category)
        })

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit logs should be read-only to preserve financial integrity.
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]