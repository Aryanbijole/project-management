from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from accounts.models import User
from projects.models import Project, Milestone
from tasks.models import TodoItem
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import Company,Group


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

    return render(
        request,
        "dashboard/group_edit.html",
        {
            "group": group,
            "companies": companies,
            "users": users,
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