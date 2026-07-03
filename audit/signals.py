from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .utils import create_audit_log


@receiver(user_logged_in)
def login_logger(sender, request, user, **kwargs):
    create_audit_log(
        request,
        module="Auth",
        action="LOGIN",
        description=f"User {user.email} logged in",
    )


@receiver(user_logged_out)
def logout_logger(sender, request, user, **kwargs):
    create_audit_log(
        request,
        module="Auth",
        action="LOGOUT",
        description=f"User {user.email} logged out",
    )