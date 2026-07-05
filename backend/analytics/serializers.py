from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'model_name', 
            'object_id', 'changes', 'description', 'ip_address', 'timestamp'
        ]
        read_only_fields = fields # All fields are read-only to prevent tampering