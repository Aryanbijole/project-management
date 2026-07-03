from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from projects.models import Project, Milestone
from tasks.models import TodoItem
from django.contrib import messages
from audit.utils import create_audit_log
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import (
    User,
    Company,
    Group,
    CompanyMembership,
    Role,
)


@login_required
def admin_reports(request):

    if not (
    request.user.is_superuser or
    request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")
    context = {
        "total_users": User.objects.count(),
        "total_projects": Project.objects.count(),
        "total_tasks": TodoItem.objects.count(),
        "completed_tasks": TodoItem.objects.filter(status="done").count(),
        "active_tasks": TodoItem.objects.exclude(status="done").count(),
        "milestones": Milestone.objects.count(),
        "recent_projects": Project.objects.order_by("-created_at")[:5],
        "recent_tasks": TodoItem.objects.order_by("-created_at")[:10],
    }

    return render(request, "dashboard/admin_reports.html", context)

@login_required
def user_list(request):

    if request.user.role != User.ROLE_ADMIN:
        return HttpResponseForbidden()

    users = User.objects.all().order_by("first_name")

    return render(
        request,
        "dashboard/users.html",
        {
            "users": users
        }
    )

@login_required
def user_create(request):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    if request.method == "POST":

        email = request.POST["email"]

        User.objects.create_user(
            username=email,
            email=email,
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            password=request.POST["password"],
            role=request.POST["role"],
        )

        messages.success(request, "User created successfully.")
        return redirect("admin_users")

    return render(request, "dashboard/user_create.html")

@login_required
def user_edit(request, user_id):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    return render(
        request,
        "dashboard/user_edit.html"
    )


@login_required
def user_delete(request, user_id):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)

    if user != request.user:
        user.delete()

    return redirect("admin_users")

@login_required
def project_list(request):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    projects = Project.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/projects.html",
        {
            "projects": projects,
        }
    )


@login_required
def project_create(request):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    return render(
        request,
        "dashboard/project_create.html"
    )


@login_required
def project_edit(request, project_id):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "dashboard/project_edit.html",
        {
            "project": project,
        }
    )


@login_required
def project_delete(request, project_id):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    project = get_object_or_404(Project, id=project_id)
    project.delete()

    return redirect("admin_project_list")


def user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user_obj.first_name = request.POST.get("first_name")
        user_obj.last_name = request.POST.get("last_name")
        user_obj.email = request.POST.get("email")
        user_obj.role = request.POST.get("role")

        role_id = request.POST.get("custom_role")

        if role_id:
            user_obj.custom_role_id = role_id
        else:
            user_obj.custom_role = None

        password = request.POST.get("password")
        if password:
            user_obj.set_password(password)

        user_obj.save()
        messages.success(request, "User updated successfully.")
        return redirect("admin_users")

    return render(
        request,
        "dashboard/user_edit.html",
        {
            "user_obj": user_obj,
            "roles": Role.objects.all(),
        },
    )


@login_required
def company_list(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden(
            "Only administrators can access this page."
        )

    companies = Company.objects.all().order_by("name")

    return render(
        request,
        "dashboard/companies.html",
        {
            "companies": companies
        }
    )

@login_required
def company_create(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden(
            "Only administrators can access this page."
        )

    if request.method == "POST":

        Company.objects.create(
            name=request.POST["name"]
        )

        messages.success(
            request,
            "Company created successfully."
        )

        return redirect("admin_company_list")

    return render(
        request,
        "dashboard/company_create.html"
    )

@login_required
def company_edit(request, company_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden(
            "Only administrators can access this page."
        )

    company = get_object_or_404(
        Company,
        id=company_id
    )

    if request.method == "POST":

        company.name = request.POST["name"]
        company.save()

        messages.success(
            request,
            "Company updated successfully."
        )

        return redirect("admin_company_list")

    return render(
        request,
        "dashboard/company_edit.html",
        {
            "company": company
        }
    )

@login_required
def company_delete(request, company_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden(
            "Only administrators can access this page."
        )

    company = get_object_or_404(
        Company,
        id=company_id
    )

    company.delete()

    messages.success(
        request,
        "Company deleted successfully."
    )

    return redirect("admin_company_list")


@login_required
def group_list(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    groups = Group.objects.select_related("company").prefetch_related("members")

    return render(
    request,
    "dashboard/group_list.html",
    {"groups": Group.objects.all()}
    )

@login_required
def group_create(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    companies = Company.objects.all()
    users = User.objects.all()

    if request.method == "POST":

        group = Group.objects.create(
            name=request.POST["name"],
            company_id=request.POST["company"],
        )

        member_ids = request.POST.getlist("members")

        group.members.set(member_ids)

        messages.success(
            request,
            "Group created successfully."
        )

        return redirect("admin_group_list")

    return render(
        request,
        "dashboard/group_create.html",
        {
            "companies": companies,
            "users": users,
        },
    )

@login_required
def group_edit(request, group_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    group = get_object_or_404(Group, id=group_id)

    companies = Company.objects.all()
    users = User.objects.all()

    if request.method == "POST":

        group.name = request.POST["name"]
        group.company_id = request.POST["company"]
        group.save()

        member_ids = request.POST.getlist("members")
        group.members.set(member_ids)

        messages.success(request, "Group updated successfully.")

        return redirect("admin_group_list")

    available_users = User.objects.exclude(
    id__in=group.members.values_list("id", flat=True)
     )
    return render(
    request,
    "dashboard/group_edit.html",
    {
        "group": group,
        "companies": companies,
        "users": users,
        "available_users": available_users,
    },
    )
@login_required
def group_delete(request, group_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    group = get_object_or_404(Group, id=group_id)

    group.delete()

    messages.success(
        request,
        "Group deleted successfully."
    )

    return redirect("admin_group_list")

@login_required
def group_detail(request, group_id):

    if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
        return HttpResponseForbidden()

    group = get_object_or_404(Group, id=group_id)

    users = User.objects.exclude(id__in=group.members.values_list("id", flat=True))

    if request.method == "POST":
        user = get_object_or_404(User, id=request.POST["user"])
        group.members.add(user)
        messages.success(request, "Member added successfully.")
        return redirect("admin_group_detail", group_id=group.id)

    return render(
        request,
        "dashboard/group_detail.html",
        {
            "group": group,
            "users": users,
        },
    )

@login_required
def remove_group_member(request, group_id, user_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden()

    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)

    group.members.remove(user)

    messages.success(request, "Member removed successfully.")

    return redirect("admin_group_detail", group_id=group.id)

@login_required
def organization_members(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    memberships = CompanyMembership.objects.select_related(
        "user",
        "company"
    )

    return render(
        request,
        "dashboard/organization_members.html",
        {
            "memberships": memberships,
        },
    )

@login_required
def organization_member_edit(request, membership_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    membership = get_object_or_404(
        CompanyMembership,
        id=membership_id
    )

    if request.method == "POST":

        membership.role = request.POST["role"]
        membership.save()

        # Keep User.role synchronized
        membership.user.role = membership.role
        membership.user.save()

        messages.success(
            request,
            "Member role updated successfully."
        )

        return redirect("organization_members")

    return render(
        request,
        "dashboard/organization_member_edit.html",
        {
            "membership": membership,
            "roles": User.ROLE_CHOICES,
        },
    )

@login_required
def organization_member_delete(request, membership_id):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    membership = get_object_or_404(
        CompanyMembership,
        id=membership_id
    )

    if request.method == "POST":

        membership.delete()

        messages.success(
            request,
            "Member removed from the organization."
        )

        return redirect("organization_members")

    return render(
        request,
        "dashboard/organization_member_delete.html",
        {
            "membership": membership,
        },
    )

@login_required
def role_list(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    roles = Role.objects.all().order_by("name")

    return render(
        request,
        "dashboard/role_list.html",
        {
            "roles": roles,
        },
    )

@login_required
def role_create(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden("Only admins can access this page.")

    if request.method == "POST":

      role = Role.objects.create(

        name=request.POST["name"],

        description=request.POST["description"],

        can_manage_users="can_manage_users" in request.POST,
        can_manage_projects="can_manage_projects" in request.POST,
        can_manage_companies="can_manage_companies" in request.POST,
        can_manage_groups="can_manage_groups" in request.POST,

        can_create_projects="can_create_projects" in request.POST,
        can_edit_projects="can_edit_projects" in request.POST,
        can_delete_projects="can_delete_projects" in request.POST,

        can_create_tasks="can_create_tasks" in request.POST,
        can_edit_tasks="can_edit_tasks" in request.POST,
        can_delete_tasks="can_delete_tasks" in request.POST,

        can_upload_files="can_upload_files" in request.POST,

        can_view_reports="can_view_reports" in request.POST,
    )

    # ✅ AUDIT LOG ADDED HERE
    create_audit_log(
        request,
        module="Role",
        action="CREATE",
        description=f"Created role '{role.name}'",
    )

    messages.success(request, "Role created successfully.")

    return redirect("admin_role_list")

@login_required
def role_edit(request, role_id):
    role = get_object_or_404(Role, id=role_id)

    if request.method == "POST":
        role.name = request.POST["name"]
        role.description = request.POST.get("description", "")
        role.save()

        create_audit_log(
            request,
            module="Role",
            action="UPDATE",
            description=f"Updated role '{role.name}'",
        )

        messages.success(request, "Role updated successfully.")
        return redirect("admin_role_list")

    return render(
        request,
        "dashboard/role_edit.html",
        {"role": role},
    )

@login_required
def role_delete(request, role_id):
    role = get_object_or_404(Role, id=role_id)

    # store name BEFORE deleting
    role_name = role.name

    role.delete()

    create_audit_log(
        request,
        module="Role",
        action="DELETE",
        description=f"Deleted role '{role_name}'",
    )

    messages.success(request, "Role deleted successfully.")
    return redirect("admin_role_list")

from audit.models import AuditLog
from django.core.paginator import Paginator


@login_required
def audit_logs(request):

    if not (
        request.user.is_superuser or
        request.user.role == User.ROLE_ADMIN
    ):
        return HttpResponseForbidden()

    logs = AuditLog.objects.select_related("user").all()

    # Search
    q = request.GET.get("q")
    if q:
        logs = logs.filter(description__icontains=q)

    # Filter by action
    action = request.GET.get("action")
    if action:
        logs = logs.filter(action=action)

    paginator = Paginator(logs, 20)

    page = request.GET.get("page")

    logs = paginator.get_page(page)

    return render(
        request,
        "dashboard/audit_logs.html",
        {
            "logs": logs,
        },
    )