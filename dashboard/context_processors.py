from accounts.models import CompanyMembership, User
from dashboard.permissions import has_company_permission


def dashboard_permissions(request):
    """
    Global template permissions.
    Available in every template that extends base.html.
    """

    if not request.user.is_authenticated:
        return {}

    membership = (
        CompanyMembership.objects
        .filter(user=request.user)
        .select_related("company")
        .first()
    )

    if not membership:
        return {
            "is_company_admin": False,
            "can_create_projects": False,
            "can_invite_members": False,
            "can_view_reports": False,
            "can_view_audit_logs": False,
        }

    company = membership.company

    return {

        "is_company_admin":
            membership.role == User.ROLE_ADMIN,

        "can_create_projects":
            has_company_permission(
                request.user,
                company,
                "can_create_projects",
            ),

        "can_invite_members":
            has_company_permission(
                request.user,
                company,
                "can_invite_members",
            ),

        "can_view_reports":
            has_company_permission(
                request.user,
                company,
                "can_view_reports",
            ),

        "can_view_audit_logs":
            has_company_permission(
                request.user,
                company,
                "can_view_audit_logs",
            ),
    }