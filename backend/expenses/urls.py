from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet, 
    TransactionViewSet, 
    AttachmentViewSet, 
    LogViewSet, 
    CategoryViewSet, 
    WalletTransferViewSet, 
    SpendViewSet,
    ExportExpensesViewSet  # ← Import the export view
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'transfers', WalletTransferViewSet, basename='wallettransfer')
router.register(r'spends', SpendViewSet, basename='spend')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'logs', LogViewSet, basename='log')
router.register(r'export', ExportExpensesViewSet, basename='export-expenses')  # ← Add this line

urlpatterns = [
    path('', include(router.urls)),
]