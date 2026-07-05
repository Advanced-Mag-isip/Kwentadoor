from django.db import models
from django.conf import settings
from .constants import BIR_CATEGORY_MAP

class TransactionsAuditLog(models.Model):
    transaction_type = models.CharField(max_length=255, blank=True)
    user = models.CharField(max_length=255, blank=True) 
    wallet = models.CharField(max_length=100, blank = True, null = True)
    category = models.CharField(max_length=100, blank = True, null = True)
    transaction_date = models.DateField(); 
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    counterparty = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    wallet_balance_before = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    wallet_balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Transaction Log'
        verbose_name_plural = 'Transaction Logs'

    def __str__(self):
        user_str = self.user.username if self.user else 'System/Anonymous'
        return f"{user_str} - {self.action} - {self.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def bir_category(self):
        """Returns the BIR mapping for this transaction's category."""
        # .get() safely returns "Uncategorized" if the category isn't in your list
        return BIR_CATEGORY_MAP.get(self.category, "Uncategorized/ Other")
