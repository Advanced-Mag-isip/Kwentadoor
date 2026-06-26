from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum
from django.forms.models import model_to_dict

from .models import Wallet, Transaction, Attachment, Log
from .serializers import WalletSerializer, TransactionSerializer, AttachmentSerializer, LogSerializer

EXPENSE_CATEGORIES = [
    {
        "id": "internet_phone",
        "label": "Internet & Phone",
        "bir_mapping": "Communication, Light and Water"
    },
    {
        "id": "office_supplies",
        "label": "Office Supplies",
        "bir_mapping": "Office Supplies"
    },
    {
        "id": "team_meals",
        "label": "Team Meals & Meetings",
        "bir_mapping": "Representation and Entertainment"
    },
    {
        "id": "software_tools",
        "label": "Software Tools & Subscriptions",
        "bir_mapping": "Professional Fees / Other Services"
    },
    {
        "id": "salaries",
        "label": "Salaries & Allowances",
        "bir_mapping": "Salaries and Wages"
    },
    {
        "id": "rent",
        "label": "Rent/Co-working Space",
        "bir_mapping": "Rental"
    },
    {
        "id": "grants_donations",
        "label": "Grants / Donations Received",
        "bir_mapping": "Grants / Donations"
    },
]

class CategoryViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing static expense categories.
    Accessed via /api/expenses/categories/
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(EXPENSE_CATEGORIES)


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Save transaction and assign the current user
        transaction = serializer.save(user=self.request.user)
        
        # Create Audit Log for Expense Creation
        Log.objects.create(
            user=self.request.user,
            action="Create Expense",
            new_data=model_to_dict(transaction)
        )

    def perform_update(self, serializer):
        # Capture old data before saving
        instance = self.get_object()
        old_data = model_to_dict(instance)
        
        # Save the updated transaction
        transaction = serializer.save()
        
        # Create Audit Log for Expense Update
        Log.objects.create(
            user=self.request.user,
            action="Update Expense",
            old_data=old_data,
            new_data=model_to_dict(transaction)
        )

    def perform_destroy(self, instance):
        old_data = model_to_dict(instance)
        
        # Create Audit Log before destroying
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
        """
        # Default to all transactions, but in a real app you'd filter by request.query_params date range
        expenses = self.get_queryset().filter(transaction_type='expense')
        
        # Total expenses for a selected period
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
        
        # Expenses by friendly category
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