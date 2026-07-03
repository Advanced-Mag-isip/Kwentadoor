from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('OTHER', 'Other'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, null=True, blank=True, help_text="The model that was affected (if any)")
    object_id = models.CharField(max_length=255, null=True, blank=True, help_text="The ID of the affected object")
    changes = models.JSONField(null=True, blank=True, help_text="A JSON payload describing the before/after changes")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField(blank=True, help_text="Human readable description of the action")

    wallet_balance_before = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    wallet_balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        user_str = self.user.username if self.user else 'System/Anonymous'
        return f"{user_str} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"