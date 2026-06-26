from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows audit logs to be viewed.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Admins can see all audit logs. Regular users can only see their own.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AuditLog.objects.all()
        return AuditLog.objects.filter(user=user)