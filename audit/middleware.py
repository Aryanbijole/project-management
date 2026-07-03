from django.utils.deprecation import MiddlewareMixin
from .utils import create_audit_log


class AuditMiddleware(MiddlewareMixin):

    def process_request(self, request):

        # Only track authenticated users
        if request.user.is_authenticated:

            # LOGIN detection (first request after login)
            if request.path == "/accounts/login/":
                return

            # Store user activity for every request (optional lightweight tracking)
            request.audit_user = request.user