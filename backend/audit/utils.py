from audit.models import AuditLog

def log_action(user, action, model_name, object_id, description, changes=None):
    """
    Unified helper to write consistently to the Audit Log.
    """
    AuditLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        action=action,          # 'CREATE', 'UPDATE', 'DELETE', 'EXPORT', 'PAYROLL', etc.
        model_name=model_name,  # 'Transaction', 'Report', 'Payroll'
        object_id=str(object_id) if object_id else None,
        description=description,
        changes=changes or {}   # {"old_data": ..., "new_data": ...}
    )