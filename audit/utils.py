from .models import AuditLog


def create_audit_log(
    request,
    module,
    action,
    description,
):

    ip = None

    if request:
        ip = request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        user=request.user if request and request.user.is_authenticated else None,
        module=module,
        action=action,
        description=description,
        ip_address=ip,
    )