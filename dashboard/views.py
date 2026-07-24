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
from dashboard.permissions import (
    can_view_reports,
    can_view_audit_logs,
)
from django.db import transaction
from django.contrib.auth import get_user_model
from projects.forms import ProjectForm
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.utils import create_notification
from audit.models import AuditLog


from accounts.decorators import (
    company_required,
    company_admin_required,
    platform_admin_required,
)
def current_company(request):
    membership = request.user.memberships.select_related("company").first()
    return membership.company if membership else None

from accounts.permissions import is_company_admin



@login_required
@company_required
@company_admin_required
def admin_reports(request):
    if request.user.is_superuser:

        projects = Project.objects.all()

        tasks = TodoItem.objects.all()

        milestones = Milestone.objects.all()

        total_users = User.objects.count()

    else:

        company = request.current_company

        projects = Project.objects.filter(
            company=company
        )

        tasks = TodoItem.objects.filter(
            todo_list__project__company=company
        )

        milestones = Milestone.objects.filter(
            project__company=company
        )

        total_users = (
            User.objects.filter(
                memberships__company=company
            )
            .distinct()
            .count()
        )
    context = {

    "total_users": total_users,

    "total_projects": projects.count(),

    "total_tasks": tasks.count(),

    "completed_tasks": tasks.filter(
        status=TodoItem.STATUS_DONE
    ).count(),

    "active_tasks": tasks.exclude(
        status=TodoItem.STATUS_DONE
    ).count(),

    "milestones": milestones.count(),

    "recent_projects": projects.order_by(
        "-created_at"
    )[:5],

    "recent_tasks": tasks.order_by(
        "-created_at"
    )[:10],

    "is_superuser_panel": request.user.is_superuser,
    }

    return render(request, "dashboard/admin_reports.html", context)

@login_required
@company_required

def user_list(request):

    if (
        not request.user.is_superuser
        and request.current_membership.role != User.ROLE_ADMIN
    ):
        return HttpResponseForbidden()


    

    if request.user.is_superuser:

        companies = Company.objects.all().order_by("name")

        selected_company = request.GET.get("company")

        if selected_company:

            users = User.objects.filter(
                memberships__company_id=selected_company
            ).distinct().order_by("first_name")

        else:

            users = User.objects.none()

    else:
        company = request.current_company

        companies = None

        selected_company = None

        users = User.objects.filter(
            memberships__company=company
        ).distinct().order_by("first_name")
        
        

    return render(
        request,
        "dashboard/users.html",
        {
            "users": users,
            "company": None if request.user.is_superuser else company,
            "companies": companies,
            "selected_company": selected_company,
            "is_superuser_panel": request.user.is_superuser,
        }
    )


@login_required
@company_required

def user_create(request):

    

    if request.user.is_superuser:

        company_id = request.GET.get("company")

        company = None

        if company_id:
            company = get_object_or_404(
                Company,
                id=company_id,
            )

    else:

        company = request.current_company

        

    if request.method == "POST":

        email = request.POST["email"]

        custom_role = None

        custom_role_id = request.POST.get("custom_role")

        if request.user.is_superuser:

            company = get_object_or_404(
                Company,
                id=request.GET.get("company")
            )
        else:

            company = request.current_company

        if custom_role_id:

            custom_role = get_object_or_404(
            Role,
            id=custom_role_id,
            company=company,
        )

        # Check whether this email already exists in this company
        existing_user = User.objects.filter(email=email).first()

        if existing_user and CompanyMembership.objects.filter(
            company=company,
            user=existing_user,
        ).exists():

            messages.warning(
                request,
                f"A user with email '{email}' already exists in this company."
            )

            return redirect("admin_users")    

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            password=request.POST["password"],
            role=request.POST["role"],
            custom_role=custom_role,
        )

        if request.user.is_superuser:

            company = get_object_or_404(
                Company,
                id=request.GET.get("company")
            )

        else:

            company = request.current_company

            CompanyMembership.objects.create(
                company=company,
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

    if request.user.is_superuser:

        companies = None

        if company:

            roles = Role.objects.filter(
                company=company
            ).order_by("name")

        else:

            roles = Role.objects.none()
    else:

        companies = None

        roles = Role.objects.filter(
            company=request.current_company
        ).order_by("name")

    return render(
        request,
        "dashboard/user_create.html",
        {
            "roles": roles,
            "companies": companies,
            "company": company,
        },
    )


@login_required
@company_required
@company_admin_required
def user_edit(request, user_id):
    if request.user.is_superuser:

        user_obj = get_object_or_404(
            User,
            id=user_id,
        )

        membership = CompanyMembership.objects.filter(
            user=user_obj
        ).first()

        company = membership.company if membership else None

    else:

        company = request.current_company

        user_obj = get_object_or_404(
            User.objects.filter(
                memberships__company=company
            ).distinct(),
            id=user_id,
        )
   

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

            target_membership = CompanyMembership.objects.filter(
                user=user_obj,
                company=company,
                role=User.ROLE_ADMIN,
            ).exists()

            if (
                not request.user.is_superuser
                and target_membership
                and request.user != user_obj
            ):

                messages.error(
                    request,
                    "Only Platform Admin can change  Company Admin's password."
                )

                return redirect("admin_users")

            user_obj.set_password(password)

        user_obj.save()

        membership = CompanyMembership.objects.filter(
            user=user_obj,
            company=company,
        ).first()

        if membership:

            membership.role = user_obj.role
            membership.save()

        create_audit_log(
            request,
            module="User",
            action="UPDATE",
            description=f"Updated user '{user_obj.email}'",
        )

        messages.success(
            request,
            "User updated successfully."
        )

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
@company_required
@company_admin_required
def user_delete(request, user_id):
    if request.user.is_superuser:

        user = get_object_or_404(
            User,
            id=user_id,
        )

        membership = CompanyMembership.objects.filter(
            user=user
        ).first()

        company = membership.company if membership else None

    else:

        company = request.current_company

        user = get_object_or_404(
            User.objects.filter(
                memberships__company=company
            ).distinct(),
            id=user_id,
        )
    

    
    
    # Prevent admin from deleting themselves

    if user.is_superuser:
        messages.error(
            request,
            "Platform administrators cannot be deleted."
        )
        return redirect("admin_users")
    

    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("admin_users")
    
    # Company Admin cannot delete another Company Admin

    target_membership = CompanyMembership.objects.filter(
        user=user,
        company=company,
        role=User.ROLE_ADMIN,
    ).exists()

    if (
        not request.user.is_superuser
        and target_membership
    ):

        messages.error(
            request,
            "Only Platform Admin can delete a Company Administrator."
        )

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
@company_admin_required
def project_list(request):

    

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")

    if request.user.is_superuser:

        company = None

        projects = (
            Project.objects.filter(
                is_archived=False
            )
            .select_related(
                "company",
                "owner",
                "created_by",
            )
        )

    else:

        company = request.current_company

        projects = (
            Project.objects.filter(
                company=company,
                is_archived=False,
            )
            .select_related(
                "company",
                "owner",
                "created_by",
            )
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

        "total_projects": (
            Project.objects.count()
            if request.user.is_superuser
            else Project.objects.filter(company=company).count()
        ),

        "active_projects": (
            Project.objects.filter(
                status=Project.STATUS_ACTIVE
            ).count()
            if request.user.is_superuser
            else Project.objects.filter(
                company=company,
                status=Project.STATUS_ACTIVE,
            ).count()
        ),

        "completed_projects": (
            Project.objects.filter(
                status=Project.STATUS_COMPLETED
            ).count()
            if request.user.is_superuser
            else Project.objects.filter(
                company=company,
                status=Project.STATUS_COMPLETED,
            ).count()
        ),

        "archived_projects": (
            Project.objects.filter(
                is_archived=True
            ).count()
            if request.user.is_superuser
            else Project.objects.filter(
                company=company,
                is_archived=True,
            ).count()
        ),
    }

    

    return render(
        request,
        "dashboard/projects.html",
        context,
    )

@login_required
@company_required
@company_admin_required
def project_create(request):

    if request.user.is_superuser:

        company = None

        company_id = (
            request.POST.get("company")
            or request.GET.get("company")
        )

        if company_id:

            company = get_object_or_404(
                Company,
                id=company_id
            )

    else:

        company = request.current_company

    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            company=company,
        )

        if form.is_valid():

            project_name = form.cleaned_data["name"].strip()

            if Project.objects.filter(
                company=company,
                name__iexact=project_name
            ).exists():

                messages.error(
                    request,
                    "A project with this name already exists."
                )

                return render(
                    request,
                    "dashboard/project_create.html",
                    {
                        "form": form,
                        "company": company,
                        "companies": Company.objects.all() if request.user.is_superuser else None,
                        "selected_company": str(company.id) if company else "",
                        "is_superuser_panel": request.user.is_superuser,
                    },
        )

            project = form.save(commit=False)

            project.company = company

            project.created_by = request.user

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
                    message=f"You have been assigned to project '{project.name}'.",
                )

            messages.success(
                request,
                "Project created successfully."
            )

            return redirect("admin_project_list")

    else:

        form = ProjectForm(company=company)

    return render(
        request,
        "dashboard/project_create.html",
        {
            "form": form,
            "company": company,
            "companies": Company.objects.all() if request.user.is_superuser else None,
            "selected_company": str(company.id) if company else "",
            "is_superuser_panel": request.user.is_superuser,
        },
    )


@login_required
@company_required
@company_admin_required
def project_edit(request, project_id):

    

    if request.user.is_superuser:

        project = get_object_or_404(
            Project,
            id=project_id,
        )

        company = project.company

    else:

        company = request.current_company

        project = get_object_or_404(
            Project,
            id=project_id,
            company=company,
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
@company_admin_required
def project_delete(request, project_id):

    

    if request.user.is_superuser:

        project = get_object_or_404(
            Project,
            id=project_id,
        )

    else:

        company = request.current_company

        project = get_object_or_404(
            Project,
            id=project_id,
            company=company,
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
@company_admin_required
def project_detail(request, project_id):

    

    project_queryset = Project.objects.select_related(
        "company",
        "owner",
        "created_by",
    ).prefetch_related("members")

    if request.user.is_superuser:

        project = get_object_or_404(
            project_queryset,
            id=project_id,
        )

    else:

        company = request.current_company

        project = get_object_or_404(
            project_queryset,
            id=project_id,
            company=company,
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
@company_admin_required
def company_list(request):

    if request.user.is_superuser:

        companies = Company.objects.all().order_by("name")

    else:

        companies = Company.objects.filter(
            id=request.current_company.id
        )

    return render(
        request,
        "dashboard/companies.html",
        {
            "companies": companies
        }
    )

from django.db import transaction

@login_required
@platform_admin_required
def company_create(request):

    if request.method == "POST":

        company_name = request.POST["name"].strip()

        admin_first_name = request.POST["admin_first_name"].strip()
        admin_last_name = request.POST["admin_last_name"].strip()

        admin_email = request.POST["admin_email"].strip().lower()
        admin_password = request.POST["admin_password"]

        # Prevent duplicate company names
        if Company.objects.filter(name__iexact=company_name).exists():

            messages.error(
                request,
                "A company with this name already exists."
            )

            return render(
                request,
                "dashboard/company_create.html"
            )

        # Prevent duplicate admin email
        if User.objects.filter(email__iexact=admin_email).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

            return render(
                request,
                "dashboard/company_create.html"
            )

        try:

            with transaction.atomic():

                # Create Company
                company = Company.objects.create(
                    name=company_name
                )

                # Create Company Admin
                admin = User.objects.create_user(
                    username=admin_email,
                    email=admin_email,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    password=admin_password,
                    role=User.ROLE_ADMIN,
                    custom_role=None,
                )

                # Assign Company Admin to Company
                CompanyMembership.objects.create(
                    company=company,
                    user=admin,
                    role=User.ROLE_ADMIN,
                )

                # Audit Log
                create_audit_log(
                    request,
                    module="Company",
                    action="CREATE",
                    description=(
                        f"Created company '{company.name}' "
                        f"with Company Admin '{admin.email}'"
                    ),
                )

            messages.success(
                request,
                "Company and Company Admin created successfully."
            )

            return redirect("admin_company_list")

        except Exception as e:

            messages.error(
                request,
                f"Company could not be created. {e}"
            )

    return render(
        request,
        "dashboard/company_create.html"
    )


@login_required
@company_required
@company_admin_required
def company_edit(request, company_id):

    if request.user.is_superuser:

        company = get_object_or_404(
            Company,
            id=company_id,
        )

    else:

        company = request.current_company

        if company.id != company_id:
            return HttpResponseForbidden()

        company = get_object_or_404(
            Company,
            id=company_id,
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
            "company": company,
        },
    )

@login_required
@platform_admin_required
def company_delete(request, company_id):

    

    company = get_object_or_404(
        Company,
        id=company_id
    )

    create_audit_log(
        request,
        module="Company",
        action="DELETE",
        description=f"Deleted company '{company.name}'",
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

    if request.user.is_superuser:

        groups = (
            Group.objects
            .select_related("company")
            .prefetch_related("members")
        )

    else:

        company = request.current_company

        groups = (
            Group.objects.filter(
                company=company
            )
            .select_related("company")
            .prefetch_related("members")
        )
   
    
    return render(
    request,
    "dashboard/group_list.html",
    {
        "groups": groups
    }
    )

@login_required
@company_admin_required
def group_create(request):

    company_id = None
    selected_company = None

    # -----------------------------
    # Superuser
    # -----------------------------
    if request.user.is_superuser:

        companies = Company.objects.all().order_by("name")

        if request.method == "POST":
            company_id = request.POST.get("company")
        else:
            company_id = request.GET.get("company")

        if company_id:

            selected_company = get_object_or_404(
                Company,
                id=company_id
            )

            users = (
                User.objects.filter(
                    memberships__company=selected_company
                )
                .distinct()
                .order_by("first_name", "last_name")
            )

        else:

            users = User.objects.none()

    # -----------------------------
    # Company Admin
    # -----------------------------
    else:

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN,
            )
            .first()
        )

        if membership is None:

            messages.error(
                request,
                "You are not authorized to create groups."
            )

            return redirect("dashboard")

        selected_company = membership.company

        companies = None

        users = (
            User.objects.filter(
                memberships__company=selected_company
            )
            .distinct()
            .order_by("first_name", "last_name")
        )

    # -----------------------------
    # Create Group
    # -----------------------------
    if request.method == "POST":

        if selected_company is None:

            messages.error(
                request,
                "Please select a company."
            )

            return redirect("admin_group_create")

        group = Group.objects.create(

            name=request.POST.get("name").strip(),

            company=selected_company,

        )

        member_ids = request.POST.getlist("members")

        if member_ids:

            group.members.set(member_ids)

        create_audit_log(
            request,
            module="Group",
            action="CREATE",
            description=f"Created group '{group.name}'",
        )

        messages.success(
            request,
            "Group created successfully."
        )

        return redirect("admin_group_list")

    return render(
        request,
        "dashboard/group_create.html",
        {
            "company": selected_company,
            "companies": companies,
            "users": users,
            "selected_company": company_id,
            "is_superuser_panel": request.user.is_superuser,
        },
    )


@login_required
@company_required
@company_admin_required
def group_edit(request, group_id):

    

    
    if request.user.is_superuser:

        group = get_object_or_404(
            Group,
            id=group_id,
        )

    else:

        company = request.current_company

        group = get_object_or_404(
            Group,
            id=group_id,
            company=company,
        )

    if request.user.is_superuser:

        companies = Company.objects.all()

    else:

        companies = Company.objects.filter(
            id=request.current_company.id
        )
    
    users = User.objects.filter(
        memberships__company=group.company
    ).distinct()

    if request.method == "POST":

        group.name = request.POST["name"]
        group.name = request.POST["name"]

        if request.user.is_superuser:
            group.company_id = request.POST["company"]
        else:
            group.company = request.current_company

        group.save()
        

        member_ids = request.POST.getlist("members")
        group.members.set(member_ids)

        create_audit_log(
            request,
            module="Group",
            action="UPDATE",
            description=f"Updated group '{group.name}'",
        )

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
@company_admin_required
def group_delete(request, group_id):


    

    if request.user.is_superuser:

        group = get_object_or_404(
            Group,
            id=group_id,
        )  

    else:

        company = request.current_company

        group = get_object_or_404(
            Group,
            id=group_id,
            company=company,
        )

    create_audit_log(
        request,
        module="Group",
        action="DELETE",
        description=f"Deleted group '{group.name}'",
    )    

    group.delete()

    messages.success(
        request,
        "Group deleted successfully."
    )

    return redirect("admin_group_list")

@login_required
@company_required
@company_admin_required
def group_detail(request, group_id):

    

    
    if request.user.is_superuser:

        group = get_object_or_404(
            Group,
            id=group_id,
        )

    else:

        company = request.current_company

        group = get_object_or_404(
            Group,
            id=group_id,
            company=company,
        )

    users = User.objects.filter(
        memberships__company=group.company
    ).exclude(
        id__in=group.members.values_list("id", flat=True)
    ).distinct().order_by("first_name")

    if request.method == "POST":
        user = get_object_or_404(
            User,
            id=request.POST["user"],
            memberships__company=group.company,
        )
        group.members.add(user)

        create_audit_log(
            request,
            module="Group",
            action="UPDATE",
            description=f"Added '{user.get_full_name() or user.email}' to group '{group.name}'",
        )

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
@company_admin_required
def remove_group_member(request, group_id, user_id):

    

    
    if request.user.is_superuser:

        group = get_object_or_404(
            Group,
            id=group_id,
        )

    else:

        company = request.current_company

        group = get_object_or_404(
            Group,
            id=group_id,
            company=company,
        )
    
    user = get_object_or_404(
        User,
        id=user_id,
        memberships__company=group.company,
    )
    group.members.remove(user)

    create_audit_log(
        request,
        module="Group",
        action="UPDATE",
        description=f"Removed '{user.get_full_name() or user.email}' from group '{group.name}'",
    )

    messages.success(request, "Member removed successfully.")

    return redirect("admin_group_detail", group_id=group.id)



@login_required
@company_required
@company_admin_required
def organization_member_edit(request, membership_id):

    if request.user.is_superuser:

        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
        )

    else:

        company = request.current_company

        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
            company=company,
        )

    # Company Admin cannot edit Platform Admin
    if (
        not request.user.is_superuser
        and membership.user.is_superuser
    ):
        messages.error(
            request,
            "You cannot modify a Platform Administrator."
        )
        return redirect("organization_members")  

    # Company Admin cannot change their own role
    if (
        not request.user.is_superuser
        and membership.user == request.user
    ):
        messages.error(
            request,
            "You cannot change your own role."
        )
        return redirect("organization_members")  


    if request.method == "POST":

        membership.role = request.POST["role"]
        membership.save()

        # Keep User.role synchronized
        membership.user.role = membership.role
        membership.user.save()

        create_audit_log(
            request,
            module="Organization",
            action="UPDATE",
            description=(
                f"Changed role of "
                f"'{membership.user.email}' "
                f"to '{membership.role}'"
            ),
        )

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
@company_admin_required
def organization_member_delete(request, membership_id):

    if request.user.is_superuser:

        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
        )

    else:

        company = request.current_company

        membership = get_object_or_404(
            CompanyMembership,
            id=membership_id,
            company=company,
        )

    # Company Admin cannot remove Platform Admin
    if (
        not request.user.is_superuser
        and membership.user.is_superuser
    ):
        messages.error(
            request,
            "You cannot remove a Platform Administrator."
        )
        return redirect("organization_members")

    # Company Admin cannot remove themselves
    if (
        not request.user.is_superuser
        and membership.user == request.user
    ):
        messages.error(
            request,
            "You cannot remove your own account."
        )
        return redirect("organization_members")

    # Prevent removing the last Company Admin
    if (
        membership.role == User.ROLE_ADMIN
    ):
        admin_count = CompanyMembership.objects.filter(
            company=membership.company,
            role=User.ROLE_ADMIN,
        ).count()

        if (
            admin_count <= 1
            and not request.user.is_superuser
        ):
            messages.error(
                request,
                "A company must always have at least one Company Admin."
            )
            return redirect("organization_members")



    if request.method == "POST":

        create_audit_log(
            request,
            module="Organization",
            action="DELETE",
            description=(
                f"Removed '{membership.user.email}' "
                f"from '{membership.company.name}'"
            ),
        )

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


from accounts.models import Role, CompanyMembership

@login_required
@company_admin_required
def role_list(request):

    if request.user.is_superuser:

        # Platform Admin -> View all companies' custom roles
        roles = (
            Role.objects
            .select_related("company")
            .all()
            .order_by("company__name", "name")
        )

    else:

        # Get the logged-in Company Admin's company
        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN,
            )
            .first()
        )

        if membership is None:

            messages.error(
                request,
                "You are not a Company Administrator."
            )

            return redirect("dashboard")

        roles = (
            Role.objects
            .select_related("company")
            .filter(company=membership.company)
            .order_by("name")
        )

    return render(
        request,
        "dashboard/role_list.html",
        {
            "roles": roles,
            "is_superuser_panel": request.user.is_superuser,
        },
    )

@login_required
@company_admin_required
def role_create(request):

    # ----------------------------
    # Decide Company
    # ----------------------------

    if request.user.is_superuser:

        company = None

        if request.method == "POST":

            company = get_object_or_404(
                Company,
                id=request.POST.get("company")
            )

    else:

        membership = request.user.memberships.filter(
            role=User.ROLE_ADMIN
        ).select_related("company").first()

        if not membership:
            messages.error(
                request,
                "No company assigned."
            )
            return redirect("dashboard")

        company = membership.company

    # ----------------------------
    # Create Role
    # ----------------------------

    if request.method == "POST":

        role_name = request.POST.get("name", "").strip()

        if Role.objects.filter(
            company=company,
            name=role_name
        ).exists():

            messages.error(
                request,
                "A role with this name already exists."
            )

            return redirect("admin_role_create")

        role = Role.objects.create(

            company=company,

            name=role_name,

            description=request.POST.get(
                "description",
                ""
            ),

            # ---------------- SAFE PERMISSIONS ----------------

            can_create_projects="can_create_projects" in request.POST,

            can_create_tasks="can_create_tasks" in request.POST,

            can_edit_tasks="can_edit_tasks" in request.POST,

            can_upload_files="can_upload_files" in request.POST,
            
            can_view_reports="can_view_reports" in request.POST,

            can_invite_members="can_invite_members" in request.POST,

            can_view_audit_logs="can_view_audit_logs" in request.POST,

            # ---------------- NEVER ALLOW ----------------

           
        )

        create_audit_log(
            request,
            module="Role",
            action="CREATE",
            description=f"Created role '{role.name}'"
        )

        messages.success(
            request,
            "Role created successfully."
        )

        return redirect("admin_role_list")
        return redirect("admin_role_list")

    # ----------------------------
    # GET
    # ----------------------------

    context = {

        "companies": Company.objects.all()
        if request.user.is_superuser
        else None,

        "is_superuser_panel": request.user.is_superuser,

    }

    return render(
        request,
        "dashboard/role_create.html",
        context,
    )


@login_required
@company_admin_required
def role_edit(request, role_id):

    # ----------------------------
    # Superuser
    # ----------------------------

    if request.user.is_superuser:

        role = get_object_or_404(
            Role,
            id=role_id,
        )

        company = role.company

    # ----------------------------
    # Company Admin
    # ----------------------------

    else:

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN,
            )
            .first()
        )

        if membership is None:

            messages.error(
                request,
                "You are not a Company Administrator."
            )

            return redirect("dashboard")

        company = membership.company

        role = get_object_or_404(
            Role,
            id=role_id,
            company=company,
        )

    # ----------------------------
    # POST
    # ----------------------------

    if request.method == "POST":

        new_name = request.POST.get("name").strip()

        if Role.objects.filter(
            company=company,
            name=new_name,
        ).exclude(
            id=role.id,
        ).exists():

            messages.error(
                request,
                "A role with this name already exists."
            )

            return redirect(
                "admin_role_edit",
                role.id,
            )

        role.name = new_name

        role.description = request.POST.get(
            "description",
            "",
        )

        # ---------- SAFE PERMISSIONS ----------

        role.can_create_projects = (
            "can_create_projects" in request.POST
        )

        role.can_edit_projects = (
            "can_edit_projects" in request.POST
        )

        role.can_create_tasks = (
            "can_create_tasks" in request.POST
        )

        role.can_edit_tasks = (
            "can_edit_tasks" in request.POST
        )

        role.can_upload_files = (
            "can_upload_files" in request.POST
        )

        role.can_view_reports = (
            "can_view_reports" in request.POST
        )

        role.can_invite_members = (
            "can_invite_members" in request.POST
        )

        role.can_view_audit_logs = (
            "can_view_audit_logs" in request.POST
        )

        # ---------- NEVER ALLOW THESE ----------

        

        role.save()

        create_audit_log(
            request,
            module="Role",
            action="UPDATE",
            description=f"Updated role '{role.name}'",
        )

        messages.success(
            request,
            "Role updated successfully.",
        )

        return redirect(
            "admin_role_list",
        )

    return render(
        request,
        "dashboard/role_edit.html",
        {
            "role": role,
            "is_superuser_panel": request.user.is_superuser,
        },
    )


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

@login_required
@company_admin_required
def role_delete(request, role_id):

    # -----------------------------
    # Superuser
    # -----------------------------
    if request.user.is_superuser:

        role = get_object_or_404(
            Role,
            id=role_id,
        )

    # -----------------------------
    # Company Admin
    # -----------------------------
    else:

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN,
            )
            .first()
        )

        if membership is None:

            messages.error(
                request,
                "You are not authorized to delete roles."
            )

            return redirect("dashboard")

        role = get_object_or_404(
            Role,
            id=role_id,
            company=membership.company,
        )

    # -----------------------------
    # POST
    # -----------------------------
    if request.method == "POST":

        role_name = role.name

        role.delete()

        create_audit_log(
            request,
            module="Role",
            action="DELETE",
            description=f"Deleted role '{role_name}'",
        )

        messages.success(
            request,
            "Role deleted successfully."
        )

        return redirect("admin_role_list")

    return render(
        request,
        "dashboard/role_delete.html",
        {
            "role": role,
        },
    )


@login_required
@company_required
@company_admin_required
def audit_logs(request):

    if request.user.is_superuser:
        logs = AuditLog.objects.select_related("user").all()
    else:
        company_users = User.objects.filter(
            memberships__company=request.current_company
        )

        logs = AuditLog.objects.filter(
            user__in=company_users
        ).select_related("user")

    q = request.GET.get("q")
    if q:
        logs = logs.filter(description__icontains=q)

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
@company_admin_required
def project_archive(request, project_id):

    if request.user.is_superuser:
        project = get_object_or_404(
            Project,
            id=project_id
        )
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            company=request.current_company
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
@company_admin_required
def archived_projects(request):

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
            company=request.current_company,
            is_archived=True
        ).select_related(
            "company",
            "owner",
            "created_by",
        )

    return render(
        request,
        "dashboard/project_archive_list.html",
        {
            "projects": projects,
        },
    )


@login_required
@company_required
@company_admin_required
def restore_project(request, project_id):

    if request.user.is_superuser:
        project = get_object_or_404(
            Project,
            id=project_id
        )
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            company=request.current_company
        )

    project.is_archived = False
    project.save()

    messages.success(
        request,
        "Project restored successfully."
    )

    return redirect("admin_archived_projects")

@login_required
@company_required
def user_project_list(request):

    if request.user.is_superuser:

        projects = Project.objects.all().distinct()

    else:

        projects = Project.objects.filter(
            company=request.current_company,
            members=request.user
        ).distinct()

    return render(
        request,
        "dashboard/projects_user.html",
        {
            "projects": projects
        }
    )

@login_required
@company_required
@can_view_reports
def company_reports(request):

    company = request.current_company

    projects = Project.objects.filter(
        company=company,
        is_archived=False
    )

    tasks = TodoItem.objects.filter(
        todo_list__project__company=company
    )

    total_projects = projects.count()

    active_projects = projects.filter(
        status=Project.STATUS_ACTIVE
    ).count()

    completed_projects = projects.filter(
        status=Project.STATUS_COMPLETED
    ).count()

    total_tasks = tasks.count()

    completed_tasks = tasks.filter(
        status=TodoItem.STATUS_DONE
    ).count()

    pending_tasks = tasks.exclude(
        status=TodoItem.STATUS_DONE
    ).count()

    context = {

        "total_projects": total_projects,

        "active_projects": active_projects,

        "completed_projects": completed_projects,

        "total_tasks": total_tasks,

        "completed_tasks": completed_tasks,

        "pending_tasks": pending_tasks,

        "projects": projects.order_by("-created_at")[:10],

    }

    return render(
        request,
        "dashboard/company_reports.html",
        context,
    )

@login_required
@company_required
@can_view_audit_logs
def company_audit_logs(request):

    company_users = User.objects.filter(
        memberships__company=request.current_company
    )

    logs = (
        AuditLog.objects
        .filter(user__in=company_users)
        .select_related("user")
        .order_by("-created_at")
    )

    q = request.GET.get("q", "")

    if q:
        logs = logs.filter(
            description__icontains=q
        )

    action = request.GET.get("action", "")

    if action:
        logs = logs.filter(
            action=action
        )

    paginator = Paginator(logs, 20)

    page = request.GET.get("page")

    logs = paginator.get_page(page)

    return render(
        request,
        "dashboard/company_audit_logs.html",
        {
            "logs": logs,
            "search": q,
            "action": action,
        },
    )