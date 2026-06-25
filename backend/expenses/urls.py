from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, TransactionViewSet, AttachmentViewSet, LogViewSet

# Initialize the DefaultRouter
router = DefaultRouter()

# Register the viewsets to automatically generate the URL routes
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'logs', LogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
]