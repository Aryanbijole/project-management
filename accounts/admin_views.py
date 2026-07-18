from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import User, CompanyMembership


from accounts.models import (
    CompanyMembership,
    Group,
    Invitation,
    Company
)

from projects.models import Project
from accounts.decorators import (
    company_required,
    company_admin_required,
    platform_admin_required,
)


@login_required
@company_required
@company_admin_required
def admin_users(request):

    # Platform Admin
    if request.user.is_superuser:

        companies = Company.objects.all().order_by("name")

        selected_company = request.GET.get("company")

        users = User.objects.none()

        if selected_company:

            users = (
                User.objects.filter(
                    memberships__company_id=selected_company
                )
                .distinct()
                .order_by("first_name")
            )

        return render(
            request,
            "accounts/admin/users_TEST.html",
            {
                "users": users,
                "companies": companies,
                "selected_company": selected_company,
                "is_superuser_panel": True,
            }
        )
    

    # Company Admin
    company = request.current_company

    users = (
        User.objects.filter(
            memberships__company=company
        )
        .distinct()
        .order_by("first_name")
    )

    return render(
        request,
        "accounts/admin/users_TEST.html",
        {
            "users": users,
            "company": company,
            "is_superuser_panel": False,
        }
    )

@login_required
@company_required
@company_admin_required
def organization_members(request):

    if request.user.is_superuser:

        memberships = (
            CompanyMembership.objects
            .select_related("user", "company")
            .order_by("company__name", "user__first_name")
        )

        return render(
            request,
            "accounts/admin/organization_members.html",
            {
                "memberships": memberships,
                "is_superuser_panel": True,
            },
        )

    company = request.current_company

    memberships = (
        CompanyMembership.objects
        .filter(company=company)
        .select_related("user", "company")
        .order_by("user__first_name")
    )

    return render(
        request,
        "accounts/admin/organization_members.html",
        {
            "company": company,
            "memberships": memberships,
            "is_superuser_panel": False,
        },
    )


@login_required
@company_required
@company_admin_required
def administration_dashboard(request):

    # Superuser
    if request.user.is_superuser:

        context = {

            "total_companies":
                CompanyMembership.objects.values(
                    "company"
                ).distinct().count(),

            "total_members":
                CompanyMembership.objects.count(),

            "total_projects":
                Project.objects.count(),

            "active_projects":
                Project.objects.filter(
                    is_archived=False
                ).count(),

            "archived_projects":
                Project.objects.filter(
                    is_archived=True
                ).count(),

            "total_groups":
                Group.objects.count(),

            "pending_invites":
                Invitation.objects.filter(
                    is_accepted=False
                ).count(),

            "is_superuser_panel": True,

        }

        return render(
            request,
            "accounts/admin/dashboard.html",
            context,
        )

    company = request.current_company

    context = {

        "company": company,

        "total_members":
            CompanyMembership.objects.filter(
                company=company
            ).count(),

        "total_projects":
            Project.objects.filter(
                company=company
            ).count(),

        "active_projects":
            Project.objects.filter(
                company=company,
                is_archived=False,
            ).count(),

        "archived_projects":
            Project.objects.filter(
                company=company,
                is_archived=True,
            ).count(),

        "total_groups":
            Group.objects.filter(
                company=company
            ).count(),

        "pending_invites":
            Invitation.objects.filter(
                company=company,
                is_accepted=False,
            ).count(),

        "is_superuser_panel": False,

    }

    return render(
        request,
        "accounts/admin/dashboard.html",
        context,
    )