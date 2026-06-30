from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import User, Wallet, Transaction, Attachment, Log, WalletTransfer, Spend
from .serializers import WalletSerializer, TransactionSerializer, AttachmentSerializer, LogSerializer, WalletTransferSerializer, SpendSerializer
from .constants import EXPENSE_CATEGORIES_DATA

from audit.models import AuditLog

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class CategoryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        return Response(EXPENSE_CATEGORIES_DATA)

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        wallet = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            model_name='Wallet',
            object_id=str(wallet.id),
            changes={'new_data': serializer.data},
            description="Created a new wallet."
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_data = self.get_serializer(instance).data
        wallet = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            model_name='Wallet',
            object_id=str(wallet.id),
            changes={'old_data': old_data, 'new_data': serializer.data},
            description="Updated a wallet."
        )

    def perform_destroy(self, instance):
        old_data = self.get_serializer(instance).data
        wallet_id = instance.id
        instance.delete()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='DELETE',
            model_name='Wallet',
            object_id=str(wallet_id),
            changes={'old_data': old_data},
            description="Deleted a wallet."
        )

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else User.objects.first()
        transaction = serializer.save(user=user)
        Log.objects.create(
            user=user,
            action="Create Expense",
            new_data=serializer.data
        )
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            model_name='Transaction',
            object_id=str(transaction.id),
            changes={'new_data': serializer.data},
            description=f"Created a new {transaction.transaction_type} transaction."
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_data = self.get_serializer(instance).data
        transaction = serializer.save()
        Log.objects.create(
            user=self.request.user if self.request.user.is_authenticated else User.objects.first(),
            action="Update Expense",
            old_data=old_data,
            new_data=serializer.data
        )
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            model_name='Transaction',
            object_id=str(transaction.id),
            changes={'old_data': old_data, 'new_data': serializer.data},
            description=f"Updated a {transaction.transaction_type} transaction."
        )

    def perform_destroy(self, instance):
        old_data = self.get_serializer(instance).data
        transaction_id = instance.id
        transaction_type = instance.transaction_type
        Log.objects.create(
            user=self.request.user if self.request.user.is_authenticated else User.objects.first(),
            action="Delete Expense",
            old_data=old_data
        )
        instance.delete()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='DELETE',
            model_name='Transaction',
            object_id=str(transaction_id),
            changes={'old_data': old_data},
            description=f"Deleted a {transaction_type} transaction."
        )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
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

class WalletTransferViewSet(viewsets.ModelViewSet):
    queryset = WalletTransfer.objects.all()
    serializer_class = WalletTransferSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        with transaction.atomic():
            wt = serializer.save()
            user = self.request.user if self.request.user.is_authenticated else User.objects.first()
            txn = Transaction.objects.create(
                transaction_type="move funds",
                user=user,
                wallet=wt.from_wallet,
                category="transfers",
                transaction_date=wt.created_at.date(),
                amount=wt.amount,
                counterparty=wt.to_wallet.name,
                wallet_transfer=wt,
            )
            wt.transaction = txn
            wt.save(update_fields=["transaction"])

class SpendViewSet(viewsets.ModelViewSet):
    queryset = Spend.objects.all()
    serializer_class = SpendSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        from datetime import datetime as dt
        with transaction.atomic():
            sp = serializer.save()
            user = self.request.user if self.request.user.is_authenticated else User.objects.first()
            tx_date_str = self.request.data.get('transaction_date', '')
            try:
                tx_date = dt.strptime(tx_date_str, '%Y-%m-%d').date() if tx_date_str else sp.created_at.date()
            except (ValueError, TypeError):
                tx_date = sp.created_at.date()
            txn = Transaction.objects.create(
                transaction_type="spend funds",
                user=user,
                wallet=sp.wallet,
                category=sp.category,
                transaction_date=tx_date,
                amount=sp.amount,
                note=self.request.data.get('note', ''),
                counterparty=self.request.data.get('counterparty', ''),
                spend=sp,
            )
            sp.transaction = txn
            sp.save(update_fields=["transaction"])

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.AllowAny]

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
