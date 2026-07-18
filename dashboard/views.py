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
from projects.forms import ProjectForm
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.utils import create_notification
from audit.models import AuditLog
from accounts.decorators import company_required
def current_company(request):
    membership = request.user.memberships.select_related("company").first()
    return membership.company if membership else None

from accounts.permissions import is_company_admin



@login_required
@company_required
def admin_reports(request):

    membership = request.user.memberships.first()

    if request.user.is_superuser:

        company = None

        projects = Project.objects.all()

        tasks = TodoItem.objects.all()

        total_users = User.objects.count()

    else:

        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

        company = membership.company

        projects = Project.objects.filter(company=company)

        tasks = TodoItem.objects.filter(
            todo_list__project__company=company
        )

        total_users = User.objects.filter(
            memberships__company=company
        ).distinct().count()

    projects = Project.objects.filter(company=company)

    tasks = TodoItem.objects.filter(
         todo_list__project__company=company
    )

    context = {
        "total_users": User.objects.filter(
        memberships__company=company
    ).distinct().count(),

        "total_projects": projects.count(),

        "total_tasks": tasks.count(),

        "completed_tasks": tasks.filter(
            status="done"
        ).count(),

        "active_tasks": tasks.exclude(
            status="done"
        ).count(),

        "milestones": Milestone.objects.filter(
            project__company=company
        ).count(),

        "recent_projects": projects.order_by("-created_at")[:5],

        "recent_tasks": tasks.order_by("-created_at")[:10],
    }

    return render(request, "dashboard/admin_reports.html", context)

@login_required
@company_required
def user_list(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    if request.user.is_superuser:

        users = User.objects.all().order_by("first_name")

    else:

        company = membership.company

        users = User.objects.filter(
            memberships__company=company
        ).distinct().order_by("first_name") 


    return render(
        request,
        "dashboard/users.html",
        {
            "users": users,
            "company": None if request.user.is_superuser else company,
            "is_superuser_panel": request.user.is_superuser,
        }
    )

@login_required
@company_required
def user_create(request):

    membership = request.user.memberships.first()

    if request.user.is_superuser:

        messages.info(
            request,
            "Create users by inviting them to a company."
        )

        return redirect("admin_users")

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    if request.method == "POST":

        email = request.POST["email"]

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            password=request.POST["password"],
            role=request.POST["role"],
        )

        CompanyMembership.objects.create(
            company=membership.company,
            user=user,
            role=user.role,
        )

        create_audit_log(
            request,
            module="User",
            action="CREATE",
            description=f"Created user '{user.email}'",
        )

        messages.success(request, "User created successfully.")
        return redirect("admin_users")

    return render(request, "dashboard/user_create.html")


@login_required
@company_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

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
    
    create_audit_log(
           request,
           module="User",
           action="UPDATE",
           description=f"Updated user '{user_obj.email}'",
    )

    return render(
        request,
        "dashboard/user_edit.html",
        {
            "user_obj": user_obj,
            "roles": Role.objects.all(),
        },
    )


@login_required
@company_required
def user_delete(request, user_id):

    

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("admin_users")

    # Save details before deletion
    email = user.email

    # Delete the user
    user.delete()

    # Create audit log
    create_audit_log(
        request,
        module="User",
        action="DELETE",
        description=f"Deleted user '{email}'",
    )

    messages.success(request, "User deleted successfully.")

    return redirect("admin_users")


@login_required
@company_required
def project_list(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")

    if request.user.is_superuser:

        company = None

        projects = Project.objects.filter(
            is_archived=False
        )

    else:

        company = membership.company

        projects = Project.objects.filter(
            company=company,
            is_archived=False
        )

    if search:
        projects = projects.filter(
            Q(name__icontains=search) |
            Q(company__name__icontains=search) |
            Q(owner__first_name__icontains=search) |
            Q(owner__last_name__icontains=search)
        )

    if status:
        projects = projects.filter(status=status)

    paginator = Paginator(projects, 10)

    page_number = request.GET.get("page")
    projects = paginator.get_page(page_number)

    context = {
        "projects": projects,
        "search": search,
        "status": status,

        "total_projects": Project.objects.filter(
            company=company
        ).count(),

        "active_projects": Project.objects.filter(
            company=company,
            status=Project.STATUS_ACTIVE
        ).count(),

        "completed_projects": Project.objects.filter(
            company=company,
            status=Project.STATUS_COMPLETED
        ).count(),

        "archived_projects": Project.objects.filter(
            company=company,
            is_archived=True
        ).count(),
    }

    return render(
        request,
        "dashboard/projects.html",
        context,
    )


@login_required
@company_required
def project_create(request):

    membership = request.user.memberships.first()

    if request.user.is_superuser:

        messages.info(
            request,
            "Please create the project from a company administration panel."
        )

        return redirect("admin_project_list")

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            company=membership.company,
        )

        if form.is_valid():

            project = form.save(commit=False)

            project.created_by = request.user

            project.company = membership.company

            project.save()

            form.save_m2m()

            create_audit_log(
                request,
                module="Project",
                action="CREATE",
                description=f"Created project '{project.name}'",
            )

            if project.owner:

              create_notification(

                user=project.owner,

                title="New Project Assigned",

                message=f"You have been assigned to project '{project.name}'."

                )

            messages.success(request, "Project created successfully.")

            return redirect("admin_project_list")

    else:

        form = ProjectForm(
            company=membership.company,
        )

    return render(
        request,
        "dashboard/project_create.html",
        {
            "form": form,
        },
    )

@login_required
@company_required
def project_edit(request, project_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    if request.user.is_superuser:

        project = get_object_or_404(
            Project,
            id=project_id
        )

        company = project.company

    else:

        company = membership.company
 
        project = get_object_or_404(
            Project,
            id=project_id,
            company=company
        )


    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            instance=project,
            company=company,
        )

        if form.is_valid():

            project = form.save()

            create_audit_log(
                request,
                module="Project",
                action="UPDATE",
                description=f"Updated project '{project.name}'",
            )

            messages.success(request, "Project updated successfully.")

            return redirect("admin_project_list")

    else:

        form = ProjectForm(
            instance=project,
            company=company,
        )

    return render(
        request,
        "dashboard/project_edit.html",
        {
            "form": form,
            "project": project,
        },
    )

@login_required
@company_required
def project_delete(request, project_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    if request.user.is_superuser:

        project = get_object_or_404(
            Project,
            id=project_id
        )

    else:

        company = membership.company

        project = get_object_or_404(
            Project,
            id=project_id,
            company=membership.company
        )


    project_name = project.name

    project.delete()

    create_audit_log(
        request,
        module="Project",
        action="DELETE",
        description=f"Deleted project '{project_name}'",
    )

    messages.success(request, "Project deleted successfully.")

    return redirect("admin_project_list")

@login_required
@company_required
def project_detail(request, project_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    project_queryset = Project.objects.select_related(
        "company",
        "owner",
        "created_by",
    ).prefetch_related("members")

    if request.user.is_superuser:

        project = get_object_or_404(
            project_queryset,
            id=project_id
        )

    else:

        project = get_object_or_404(
            project_queryset,
            id=project_id,
            company=membership.company
        )

    tasks = TodoItem.objects.filter(
        todo_list__project=project
    )

    total_tasks = tasks.count()

    completed_tasks = tasks.filter(
        status=TodoItem.STATUS_DONE
    ).count()

    pending_tasks = total_tasks - completed_tasks

    progress = (
        int((completed_tasks / total_tasks) * 100)
        if total_tasks else 0
    )

    recent_tasks = tasks.order_by("-created_at")[:5]

    context = {
        "project": project,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "progress": progress,
        "recent_tasks": recent_tasks,
    }

    return render(
        request,
        "dashboard/project_detail.html",
        context,
    )

@login_required
@company_required
def company_list(request):

    

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    if request.user.is_superuser:
        companies = Company.objects.all().order_by("name")
    else:
        companies = Company.objects.filter(
            id=membership.company.id
        )

    return render(
        request,
        "dashboard/companies.html",
        {
            "companies": companies
        }
    )

@login_required
@company_required
def company_create(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only Platform Admin can create companies."
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
@company_required
def company_edit(request, company_id):

    

    membership = request.user.memberships.first()

    if request.user.is_superuser:
        company = get_object_or_404(
            Company,
            id=company_id
        )
    else:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

        company = membership.company

        if company.id != company_id:
            return HttpResponseForbidden()

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
@company_required
def company_delete(request, company_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only Platform Admin can delete companies."
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
@company_required
def group_list(request):

   
    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden("Access denied.")

    if request.user.is_superuser:
        groups = Group.objects.select_related(
            "company"
        ).prefetch_related("members")
    else:
        groups = Group.objects.filter(
            company=membership.company
        ).select_related(
            "company"
        ).prefetch_related("members")

    return render(
    request,
    "dashboard/group_list.html",
    {
        "groups": groups
    }
    )

@login_required
@company_required
def group_create(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        
    membership = request.user.memberships.first()

    if request.user.is_superuser:

        messages.info(
            request,
            "Groups are created inside a company."
        )

        return redirect("admin_group_list")

    company = membership.company


    users = User.objects.filter(
        memberships__company=company
    ).distinct()

    if request.method == "POST":

        group = Group.objects.create(
            name=request.POST["name"],
            company=company,
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
            "company": company,
            "users": users,
        },
    )

@login_required
@company_required
def group_edit(request, group_id):

    

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden("Access denied.")

    if request.user.is_superuser:
        group = get_object_or_404(
            Group,
            id=group_id
        )
    else:
        group = get_object_or_404(
            Group,
            id=group_id,
            company=membership.company
        )

    if request.user.is_superuser:
        companies = Company.objects.all()
    else:
        companies = Company.objects.filter(
            id=membership.company.id
        )
    
    users = User.objects.filter(
        memberships__company=group.company
    ).distinct()

    if request.method == "POST":

        group.name = request.POST["name"]
        group.company_id = request.POST["company"]
        group.save()

        member_ids = request.POST.getlist("members")
        group.members.set(member_ids)

        messages.success(request, "Group updated successfully.")

        return redirect("admin_group_list")

    available_users = User.objects.filter(
        memberships__company=group.company
    ).exclude(
        id__in=group.members.values_list("id", flat=True)
    ).distinct()
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
@company_required
def group_delete(request, group_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    membership = request.user.memberships.first()

    if request.user.is_superuser:
        group = get_object_or_404(
            Group,
            id=group_id
        )
    else:
        group = get_object_or_404(
            Group,
            id=group_id,
            company=membership.company
        )

    group.delete()

    messages.success(
        request,
        "Group deleted successfully."
    )

    return redirect("admin_group_list")

@login_required
@company_required
def group_detail(request, group_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()

    membership = request.user.memberships.first()

    if request.user.is_superuser:
        group = get_object_or_404(
            Group,
            id=group_id
        )
    else:
        group = get_object_or_404(
            Group,
            id=group_id,
            company=membership.company
        )

    users = User.objects.filter(
        memberships__company=group.company
    ).exclude(
        id__in=group.members.values_list("id", flat=True)
    ).distinct()

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
@company_required
def remove_group_member(request, group_id, user_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    membership = request.user.memberships.first()

    if request.user.is_superuser:
        group = get_object_or_404(
            Group,
            id=group_id
        )
    else:
        group = get_object_or_404(
            Group,
            id=group_id,
            company=membership.company
        )
    user = get_object_or_404(User, id=user_id)

    group.members.remove(user)

    messages.success(request, "Member removed successfully.")

    return redirect("admin_group_detail", group_id=group.id)

@login_required
@company_required
def organization_members(request):

    

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden("Access denied.")
    
    if request.user.is_superuser:
        memberships = CompanyMembership.objects.select_related(
            "user",
            "company"
        )
    else:
        memberships = CompanyMembership.objects.filter(
            company=membership.company
        ).select_related(
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
@company_required
def organization_member_edit(request, membership_id):

    membership = request.user.memberships.first()

    admin_membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not admin_membership or admin_membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden("Access denied.")

    if request.user.is_superuser:
        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id
        )
    else:
        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
            company=admin_membership.company
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
@company_required
def organization_member_delete(request, membership_id):

    membership = request.user.memberships.first()

    admin_membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not admin_membership or admin_membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden("Access denied.")

    if request.user.is_superuser:
        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id
        )
    else:
        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
            company=admin_membership.company
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
@company_required
def role_list(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        
    roles = Role.objects.all().order_by("name")

    return render(
        request,
        "dashboard/role_list.html",
        {
            "roles": roles,
        },
    )

@login_required
@company_required
def role_create(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

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

        create_audit_log(
            request,
            module="Role",
            action="CREATE",
            description=f"Created role '{role.name}'",
        )

        messages.success(request, "Role created successfully.")

        return redirect("admin_role_list")

    return render(
        request,
        "dashboard/role_create.html",
    )

@login_required
@company_required
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
@company_required
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



@login_required
@company_required
def audit_logs(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    if request.user.is_superuser:
        logs = AuditLog.objects.select_related("user").all()
    else:
        company_users = User.objects.filter(
            memberships__company=membership.company
        )

        logs = AuditLog.objects.filter(
            user__in=company_users
        ).select_related("user")

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

@login_required
@company_required
def project_archive(request, project_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        
    if request.user.is_superuser:
        project = get_object_or_404(
            Project,
            id=project_id
        )
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            company=membership.company
        )
    project.is_archived = not project.is_archived
    project.save()

    if project.is_archived:

        create_notification(
        user=project.owner,
        title="Project Archived",
        message=f"Project '{project.name}' has been archived."
    )

    else:

        create_notification(
        user=project.owner,
        title="Project Restored",
        message=f"Project '{project.name}' has been restored."
    )

    if project.is_archived:
        action = "ARCHIVE"
        message = "Project archived successfully."
    else:
        action = "UNARCHIVE"
        message = "Project restored successfully."

    create_audit_log(
        request,
        module="Project",
        action=action,
        description=f"{action.title()} project '{project.name}'",
    )

    messages.success(request, message)

    return redirect("admin_project_list")

@login_required
@company_required
def archived_projects(request):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    if request.user.is_superuser:
        projects = Project.objects.filter(
            is_archived=True
        ).select_related(
           "company",
            "owner",
            "created_by",
        )
    else:
        projects = Project.objects.filter(
            company=membership.company,
            is_archived=True
        ).select_related(
            "company",
            "owner",
            "created_by",
        )

    context = {
        "projects": projects,
    }

    return render(
        request,
        "dashboard/project_archive_list.html",
        context,
    )

@login_required
@company_required
def restore_project(request, project_id):

    membership = request.user.memberships.first()

    if not request.user.is_superuser:
        if not membership or membership.role != User.ROLE_ADMIN:
            return HttpResponseForbidden()
        

    if request.user.is_superuser:
        project = get_object_or_404(
            Project,
            id=project_id
        )
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            company=membership.company
        )

    project.is_archived = False
    project.save()

    messages.success(
        request,
        "Project restored successfully."
    )

    return redirect(
        "admin_archived_projects"
    )


@login_required
@company_required
def user_project_list(request):

    if request.user.is_superuser:

        projects = Project.objects.all().distinct()

    else:

        membership = request.user.memberships.first()

        projects = Project.objects.filter(
            company=membership.company,
            members=request.user
        ).distinct()

    return render(

        request,

        "dashboard/projects_user.html",

        {
            "projects": projects
        }

    )