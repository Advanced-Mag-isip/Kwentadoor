from django.contrib import admin
from .models import Wallet, Transaction, Attachment, Log, User

# Register your models here.
admin.site.register(User)
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_type", "user", "wallet", "category", "amount", "transaction_date", 'wallet_balance_before', 'wallet_balance_after']
    list_filter = ["transaction_type", "category", "transaction_date", "wallet"]
    search_fields = ["note", "counterparty"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction", "created_at"]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "created_at"]
    list_filter = ["action"]
    readonly_fields = ["user", "action", "old_data", "new_data", "created_at"]
