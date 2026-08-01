from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from accounts.models import CompanyMembership, User


def has_company_permission(user, company, permission_name):
    """
    Returns True if the user has the requested permission
    through Superuser, Company Admin or Custom Role.
    """

    if user.is_superuser:
        return True

    membership = CompanyMembership.objects.filter(
        user=user,
        company=company
    ).first()

    if not membership:
        return False

    # Company Admin has all permissions
    if membership.role == User.ROLE_ADMIN:
        return True

    role = user.custom_role

    if not role:
        return False

    return getattr(role, permission_name, False)


def permission_required(permission_name):
    """
    Allows access if:
    1. Superuser
    2. Company Admin
    3. Custom Role has the requested permission
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # -------------------------
            # Superuser
            # -------------------------

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            membership = CompanyMembership.objects.filter(
                user=request.user
            ).first()

            if not membership:
                messages.error(request, "You are not assigned to any company.")
                return redirect("dashboard")

            # -------------------------
            # Company Admin
            # -------------------------

            if membership.role == User.ROLE_ADMIN:
                return view_func(request, *args, **kwargs)

            # -------------------------
            # Custom Role
            # -------------------------

            role = request.user.custom_role
            if role and getattr(role, permission_name, False):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "You don't have permission to perform this action."
            )

            return redirect("dashboard")

        return wrapper

    return decorator


# -------------------------------------------------
# Ready-to-use decorators
# -------------------------------------------------

can_create_projects = permission_required(
    "can_create_projects"
)

can_invite_members = permission_required(
    "can_invite_members"
)

can_view_reports = permission_required(
    "can_view_reports"
)

can_view_audit_logs = permission_required(
    "can_view_audit_logs"
)