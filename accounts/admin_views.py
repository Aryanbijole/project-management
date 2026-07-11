from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import User, CompanyMembership


from accounts.models import (
    CompanyMembership,
    Group,
    Invitation,
)

from projects.models import Project

@login_required
def admin_users(request):

    # Superuser
    if request.user.is_superuser:

        users = User.objects.all().order_by("first_name")

        return render(
            request,
            "accounts/admin/users.html",
            {
                "users": users,
                "is_superuser_panel": True,
            }
        )

    # Company Admin
    membership = CompanyMembership.objects.filter(
        user=request.user,
        role=User.ROLE_ADMIN
    ).first()

    if membership:

        company = membership.company

        users = User.objects.filter(
            memberships__company=company
        ).distinct().order_by("first_name")

        return render(
            request,
            "accounts/admin/users.html",
            {
                "users": users,
                "company": company,
                "is_superuser_panel": False,
            }
        )

    messages.error(
        request,
        "You don't have permission to access this page."
    )

    return redirect("dashboard")

@login_required
def organization_members(request):

    # Superuser
    if request.user.is_superuser:

        memberships = (
            CompanyMembership.objects
            .select_related(
                "user",
                "company",
            )
            .order_by(
                "company__name",
                "user__first_name",
            )
        )

        return render(
            request,
            "accounts/admin/organization_members.html",
            {
                "memberships": memberships,
                "is_superuser_panel": True,
            },
        )

    # Company Admin
    membership = CompanyMembership.objects.filter(
        user=request.user,
        role=User.ROLE_ADMIN,
    ).first()

    if membership:

        company = membership.company

        memberships = (
            CompanyMembership.objects
            .filter(company=company)
            .select_related(
                "user",
                "company",
            )
            .order_by(
                "user__first_name",
            )
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

    messages.error(
        request,
        "You don't have permission to access this page.",
    )

    return redirect("dashboard")

@login_required
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

    membership = CompanyMembership.objects.filter(
        user=request.user,
        role="admin",
    ).first()

    if not membership:

        messages.error(
            request,
            "Access denied."
        )

        return redirect("dashboard")

    company = membership.company

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