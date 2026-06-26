from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import CATEGORY_CHOICES, TRANSACTION_TYPE_CHOICES

class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

class Wallet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    @property
    def balance(self):
        """Dynamically calculates the wallet balance based on related transactions."""
        additions = self.transactions.filter(transaction_type='add funds').aggregate(models.Sum('amount'))['amount__sum'] or 0
        deductions = self.transactions.filter(transaction_type='spend funds').aggregate(models.Sum('amount'))['amount__sum'] or 0
        return additions - deductions
    
class Transaction(models.Model):
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transactions")
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    counterparty = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-transaction_date"]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"

class Attachment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="attachments")
    reference_number = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(blank=True, null=True, upload_to="attachments/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"

    def __str__(self):
        return f"Attachment #{self.id}"

class Log(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="logs")
    action = models.CharField(max_length=50)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "logs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.action