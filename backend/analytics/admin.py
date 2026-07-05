from django.contrib import admin
from .models import TransactionsAuditLog

@admin.register(TransactionsAuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["transaction_type", "user", "wallet", "category", "amount", "transaction_date", "counterparty", "note", 'wallet_balance_before', 'wallet_balance_after']
    list_filter = ["transaction_type", "category", "transaction_date", "wallet"]
    search_fields = ["note", "counterparty"]
    
    # Prevent creation, modification, and deletion in the admin panel
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False