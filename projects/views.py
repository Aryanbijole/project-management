from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Company, User
from projects.models import Project, ProjectTool
from integrations.models import ExternalTool
from django.views.generic import ListView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Project, Milestone, ProjectDocument, ProjectActivity
from django.core.mail import send_mail
from django.conf import settings
from .models import ProjectInvitation,ProjectDocument
from tasks.models import TodoItem
from django.db.models import Q
from accounts.models import Notification
from .forms import ProjectDocumentForm
from django.http import FileResponse
from projects.forms import ProjectForm
from audit.models import AuditLog
from accounts.decorators import company_required
from audit.utils import create_audit_log
from accounts.models import CompanyMembership
from dashboard.permissions import has_company_permission
from dashboard.permissions import (
    can_create_projects,
    
)


class ProjectListView(ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):

        user = self.request.user

        if user.is_superuser:
            return Project.objects.all()

        membership = CompanyMembership.objects.filter(
            user=user
        ).first()

        if not membership:
            return Project.objects.none()

        return Project.objects.filter(
            company=membership.company
        )
    
class ProjectCreateView(CreateView):
    model = Project
    fields = [
        'name',
        'description',
        'company',
        'owner',
        'visibility',
        'status'
    ]
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project-list')

@login_required
@company_required
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members')
        membership = request.user.memberships.first()
        company = membership.company


        if name:
            project = Project.objects.create(
                name=name,
                description=description,
                company=company,
                created_by=request.user
            )

            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                action="Project Created",
                description=f"{request.user.get_full_name() or request.user.username} created the project '{project.name}'."
            )
            # Add creator as member
            project.members.add(request.user)
            if member_ids:
                users = User.objects.filter(id__in=member_ids)
                project.members.add(*users)
                
            messages.success(request, f"Project '{name}' created successfully!")
            return redirect('project_detail', project_id=project.id)
        else:
            messages.error(request, "Project name is required.")
            
    return redirect('dashboard')


@login_required
@company_required
def project_detail(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )
    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                 request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != "admin":

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this project."
                )
                return redirect("dashboard")
            
    # Get tools
    tools = project.tools.all()
    enabled_tools = tools.filter(is_enabled=True)
    
    # Check which tools are enabled to render buttons
    enabled_keys = [t.tool_key for t in enabled_tools]
    
    # Get tools names (dynamic copy in DB)
    tool_names = {t.tool_key: t.name for t in tools}

    # External tools
    external_tools = ExternalTool.objects.filter(project=project)
    
    # Company members not in project (to invite/add to project)
    company_users = User.objects.filter(
        memberships__company=project.company, 
        is_active=True
    ).exclude(id__in=project.members.all())

    milestones = project.milestones.all()

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'tools': tools,
        'enabled_keys': enabled_keys,
        'tool_names': tool_names,
        'external_tools': external_tools,
        'company_users': company_users,
        'milestones': milestones,
    })


@login_required
@company_required
def add_project_member(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        # Only Company Admin can add members
        if membership.role != User.ROLE_ADMIN:
            messages.error(
                request,
                "Only the Company Admin can add project members."
            )
            return redirect(
                "project_detail",
                project_id=project.id
            )

    # -----------------------------------------
    # Add Member
    # -----------------------------------------

    if request.method == "POST":

        user_id = request.POST.get("user_id")

        if user_id:

            # Superuser can add anyone
            if request.user.is_superuser:

                user = get_object_or_404(
                    User,
                    id=user_id,
                    is_active=True,
                )

            # Company Admin can only add users from their company
            else:

                user = get_object_or_404(
                    User,
                    id=user_id,
                    memberships__company=project.company,
                    is_active=True,
                )

            project.members.add(user)

            messages.success(
                request,
                f"{user.get_full_name() or user.email} added to the project successfully."
            )

        else:

            messages.error(
                request,
                "No user was selected."
            )

    return redirect(
        "project_detail",
        project_id=project.id
    )


@login_required
@company_required
def configure_tools(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to the company
        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        is_admin = membership.role == User.ROLE_ADMIN
        is_creator = project.created_by == request.user

        if not (is_admin or is_creator):
            messages.error(
                request,
                "Only the Project Creator or Company Admin can configure project tools."
            )
            return redirect(
                "project_detail",
                project_id=project.id
            )

    # --------------------------------------------------
    # Configure Tools
    # --------------------------------------------------

    tools = project.tools.all()

    if request.method == "POST":

        for tool in tools:

            tool.is_enabled = (
                request.POST.get(f"enabled_{tool.tool_key}") == "on"
            )

            custom_name = request.POST.get(
                f"name_{tool.tool_key}",
                tool.name
            ).strip()

            if custom_name:
                tool.name = custom_name

            tool.save()

        messages.success(
            request,
            "Project tools configured successfully!"
        )

        return redirect(
            "project_detail",
            project_id=project.id
        )

    return render(
        request,
        "projects/configure_tools.html",
        {
            "project": project,
            "tools": tools,
        },
    )

@login_required
@company_required
def invite_project_member(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        is_admin = membership.role == User.ROLE_ADMIN
        is_creator = project.created_by == request.user

        if not (is_admin or is_creator):
            messages.error(
                request,
                "Only the Project Creator or Company Admin can invite members."
            )
            return redirect(
                "project_detail",
                project_id=project.id
            )

    # --------------------------------------------------
    # Send Invitation
    # --------------------------------------------------

    if request.method == "POST":

        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(
                request,
                "Please enter an email address."
            )
            return redirect(
                "project_detail",
                project_id=project.id
            )

        invite = ProjectInvitation.objects.create(
            project=project,
            email=email,
            invited_by=request.user
        )

        invite_link = (
            f"http://127.0.0.1:8000/"
            f"invitations/{invite.token}/"
        )

        send_mail(
            subject="Project Invitation",
            message=f"""
You have been invited to join the project:

Project: {project.name}

Invitation Link:

{invite_link}
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(
            request,
            "Invitation email sent successfully."
        )

    return redirect(
        "project_detail",
        project_id=project.id
    )


@login_required
def accept_invitation(request, token):

    invite = get_object_or_404(
        ProjectInvitation,
        token=token,
        accepted=False
    )

    # -----------------------------------------
    # Only invited email can accept
    # -----------------------------------------

    if request.user.email.lower() != invite.email.lower():

        messages.error(
            request,
            "This invitation was sent to another email address."
        )

        return redirect("dashboard")

    from accounts.models import CompanyMembership

    # -----------------------------------------
    # Company Membership
    # -----------------------------------------

    membership, created = CompanyMembership.objects.get_or_create(
        company=invite.project.company,
        user=request.user,
        defaults={
            "role": User.ROLE_MEMBER
        },
    )

    # -----------------------------------------
    # Add to Project
    # -----------------------------------------

    invite.project.members.add(request.user)

    # -----------------------------------------
    # Mark Invitation Accepted
    # -----------------------------------------

    invite.accepted = True
    invite.save()

    messages.success(
        request,
        f"You have successfully joined '{invite.project.name}'."
    )

    return redirect(
        "project_detail",
        project_id=invite.project.id
    )

@login_required
@company_required
def add_milestone(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        is_admin = membership.role == User.ROLE_ADMIN
        is_creator = project.created_by == request.user

        if not (is_admin or is_creator):
            messages.error(
                request,
                "Only the Project Creator or Company Admin can create milestones."
            )
            return redirect(
                "project_detail",
                project_id=project.id
            )

    # --------------------------------------------------
    # Create Milestone
    # --------------------------------------------------

    if request.method == "POST":

        milestone = Milestone.objects.create(
            project=project,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            due_date=request.POST.get("due_date")
        )

        # Notify project members
        for member in project.members.all():

            if member != request.user:

                Notification.objects.create(
                    user=member,
                    title="New Milestone",
                    message=(
                        f"Milestone '{milestone.title}' "
                        f"was added to project '{project.name}'."
                    )
                )

        messages.success(
            request,
            "Milestone created successfully."
        )

    return redirect(
        "project_detail",
        project_id=project.id
    )


@login_required
@company_required
def analytics_dashboard(request):

    # =====================================================
    # SUPERUSER
    # =====================================================

    if request.user.is_superuser:

        total_projects = Project.objects.count()

        total_tasks = TodoItem.objects.count()

        completed_tasks = TodoItem.objects.filter(
            status="done"
        ).count()

        total_members = User.objects.filter(
            is_superuser=False
        ).count()

        companies = Company.objects.all().order_by("name")

        selected_company = None
        company_projects = Project.objects.none()

        company_id = request.GET.get("company")

        if company_id:

            selected_company = get_object_or_404(
                Company,
                id=company_id
            )

            company_projects = Project.objects.filter(
                company=selected_company
            ).order_by("name")

    # =====================================================
    # COMPANY USERS
    # =====================================================

    else:

        company = request.current_company

        total_projects = Project.objects.filter(
            company=company
        ).count()

        total_tasks = TodoItem.objects.filter(
            todo_list__project__company=company
        ).count()

        completed_tasks = TodoItem.objects.filter(
            todo_list__project__company=company,
            status="done"
        ).count()

        total_members = User.objects.filter(
            memberships__company=company
        ).distinct().count()

        companies = None
        selected_company = company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # Company Admin
        if membership and membership.role == User.ROLE_ADMIN:

            company_projects = Project.objects.filter(
                company=company
            ).order_by("name")

        # Normal Member
        else:

            company_projects = Project.objects.filter(
                company=company,
                members=request.user
            ).distinct().order_by("name")

    # =====================================================
    # OVERALL COMPLETION
    # =====================================================

    pending_tasks = total_tasks - completed_tasks

    completion_percentage = 0

    if total_tasks:

        completion_percentage = round(
            (completed_tasks / total_tasks) * 100,
            2
        )

    # =====================================================
    # PROJECT ANALYTICS
    # =====================================================

    selected_project = None

    project_total_tasks = 0
    project_completed_tasks = 0
    project_pending_tasks = 0
    project_completion_percentage = 0

    project_total_milestones = 0
    completed_milestones = 0

    project_members = 0

    project_id = request.GET.get("project")

    if project_id:

        if request.user.is_superuser:

            selected_project = get_object_or_404(
                Project,
                id=project_id
            )

        else:

            membership = request.user.memberships.filter(
                company=request.current_company
            ).first()

            if membership and membership.role == User.ROLE_ADMIN:

                selected_project = get_object_or_404(
                    Project,
                    id=project_id,
                    company=request.current_company
                )

            else:

                selected_project = get_object_or_404(
                    Project,
                    id=project_id,
                    company=request.current_company,
                    members=request.user
                )

        project_total_tasks = TodoItem.objects.filter(
            todo_list__project=selected_project
        ).count()

        project_completed_tasks = TodoItem.objects.filter(
            todo_list__project=selected_project,
            status="done"
        ).count()

        project_pending_tasks = (
            project_total_tasks - project_completed_tasks
        )

        if project_total_tasks:

            project_completion_percentage = round(
                (
                    project_completed_tasks /
                    project_total_tasks
                ) * 100,
                2
            )

        project_completion = None

        if selected_project:

            project_tasks = TodoItem.objects.filter(
                todo_list__project=selected_project
            )

            project_total_tasks = project_tasks.count()

            project_completed_tasks = project_tasks.filter(
                status="done"
            ).count()

            project_pending_tasks = (
                project_total_tasks -
                project_completed_tasks
            )

            if project_total_tasks > 0:
                project_completion = round(
                    (project_completed_tasks / project_total_tasks) * 100,
                    2
                )
            else:
                project_completion = 0

    # =====================================================
    # TEMPLATE
    # =====================================================

    return render(
        request,
        "projects/analytics.html",
        {
            # Overall Analytics
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_percentage": completion_percentage,
            "total_members": total_members,

            # Company Selection
            "companies": companies,
            "selected_company": selected_company,

            # Project Selection
            "company_projects": company_projects,
            "selected_project": selected_project,

            # Project Analytics
            "project_total_tasks": project_total_tasks,
            "project_completed_tasks": project_completed_tasks,
            "project_pending_tasks": project_pending_tasks,
            "project_completion_percentage": project_completion_percentage,


            "project_members": project_members,
        }
    )

@login_required
@company_required
def calendar_view(request):

    # --------------------------------------------------
    # Superuser
    # --------------------------------------------------

    if request.user.is_superuser:

        tasks = (
            TodoItem.objects
            .exclude(due_date__isnull=True)
            .select_related(
                "todo_list",
                "todo_list__project"
            )
        )

        milestones = Milestone.objects.select_related(
            "project"
        )

    # --------------------------------------------------
    # Company Users
    # --------------------------------------------------

    else:

        company = request.current_company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # ----------------------------------------------
        # Company Admin
        # ----------------------------------------------

        if membership and membership.role == User.ROLE_ADMIN:

            tasks = (
                TodoItem.objects
                .filter(
                    todo_list__project__company=company
                )
                .exclude(
                    due_date__isnull=True
                )
                .select_related(
                    "todo_list",
                    "todo_list__project"
                )
            )

            milestones = Milestone.objects.filter(
                project__company=company
            ).select_related(
                "project"
            )

        # ----------------------------------------------
        # Company Member
        # ----------------------------------------------

        else:

            tasks = (
                TodoItem.objects
                .filter(
                    todo_list__project__company=company,
                    todo_list__project__members=request.user
                )
                .exclude(
                    due_date__isnull=True
                )
                .distinct()
                .select_related(
                    "todo_list",
                    "todo_list__project"
                )
            )

            milestones = Milestone.objects.filter(
                project__company=company,
                project__members=request.user
            ).distinct().select_related(
                "project"
            )

    return render(
        request,
        "projects/calendar.html",
        {
            "tasks": tasks,
            "milestones": milestones,
        },
    )


@login_required
@company_required
def global_search(request):

    query = request.GET.get("q", "").strip()

    projects = Project.objects.none()
    tasks = TodoItem.objects.none()
    users = User.objects.none()
    milestones = Milestone.objects.none()
    documents = ProjectDocument.objects.none()

    # ==================================================
    # SUPERUSER
    # ==================================================

    if request.user.is_superuser:

        projects = Project.objects.filter(
            name__icontains=query
        )

        tasks = TodoItem.objects.filter(
            title__icontains=query
        )

        users = User.objects.filter(
            email__icontains=query
        )

        milestones = Milestone.objects.filter(
            title__icontains=query
        )

        documents = ProjectDocument.objects.filter(
            title__icontains=query
        )

    # ==================================================
    # COMPANY USERS
    # ==================================================

    else:

        company = request.current_company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # ------------------------------------------
        # Company Admin
        # ------------------------------------------

        if membership and membership.role == User.ROLE_ADMIN:

            projects = Project.objects.filter(
                company=company,
                name__icontains=query
            )

            tasks = TodoItem.objects.filter(
                todo_list__project__company=company,
                title__icontains=query
            )

            users = User.objects.filter(
                memberships__company=company,
                email__icontains=query
            ).distinct()

            milestones = Milestone.objects.filter(
                project__company=company,
                title__icontains=query
            )

            documents = ProjectDocument.objects.filter(
                project__company=company,
                title__icontains=query
            )

        # ------------------------------------------
        # Normal Member
        # ------------------------------------------

        else:

            projects = Project.objects.filter(
                company=company,
                members=request.user,
                name__icontains=query
            ).distinct()

            tasks = TodoItem.objects.filter(
                todo_list__project__company=company,
                todo_list__project__members=request.user,
                title__icontains=query
            ).distinct()

            milestones = Milestone.objects.filter(
                project__company=company,
                project__members=request.user,
                title__icontains=query
            ).distinct()

            documents = ProjectDocument.objects.filter(
                project__company=company,
                project__members=request.user,
                title__icontains=query
            ).distinct()

    return render(
        request,
        "projects/search.html",
        {
            "query": query,
            "projects": projects,
            "tasks": tasks,
            "users": users,
            "milestones": milestones,
            "documents": documents,
        },
    )



@login_required
@company_required
def project_document_upload(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        is_admin = membership.role == User.ROLE_ADMIN
        is_creator = project.created_by == request.user

        if not (is_admin or is_creator):

            messages.error(
                request,
                "Only the Project Creator or Company Admin can upload documents."
            )

            return redirect(
                "project_detail",
                project_id=project.id
            )

    # --------------------------------------------------
    # Upload
    # --------------------------------------------------

    if request.method == "POST":

        form = ProjectDocumentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            document = form.save(commit=False)

            document.project = project
            document.uploaded_by = request.user

            document.save()

            messages.success(
                request,
                "Document uploaded successfully."
            )

            return redirect(
                "project_documents",
                project_id=project.id
            )

    else:

        form = ProjectDocumentForm()

    return render(
        request,
        "projects/document_upload.html",
        {
            "project": project,
            "form": form,
        },
    )

@login_required
@company_required
def project_documents(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:

            messages.error(
                request,
                "Access denied."
            )

            return redirect("dashboard")

        # Company Admin
        if membership.role != User.ROLE_ADMIN:

            # Normal member must belong to the project
            if not project.members.filter(id=request.user.id).exists():

                messages.error(
                    request,
                    "You are not authorized to view these project documents."
                )

                return redirect("dashboard")

    # --------------------------------------------------
    # Documents
    # --------------------------------------------------

    documents = (
        ProjectDocument.objects
        .filter(project=project)
        .select_related("uploaded_by")
        .order_by("-uploaded_at")
    )

    return render(
        request,
        "projects/document_list.html",
        {
            "project": project,
            "documents": documents,
            "membership": None if request.user.is_superuser else membership,
        }
    )

@login_required
@company_required
def download_document(request, document_id):

    document = get_object_or_404(
        ProjectDocument,
        id=document_id
    )

    project = document.project

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:

            messages.error(
                request,
                "Access denied."
            )

            return redirect("dashboard")

        # Company Admin
        if membership.role != User.ROLE_ADMIN:

            # Normal members must belong to project
            if not project.members.filter(
                id=request.user.id
            ).exists():

                messages.error(
                    request,
                    "You are not authorized to download this document."
                )

                return redirect("dashboard")

    # --------------------------------------------------
    # Download
    # --------------------------------------------------

    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.filename,
    )

@login_required
@company_required
def delete_document(request, document_id):

    document = get_object_or_404(
        ProjectDocument,
        id=document_id
    )

    project = document.project

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:

            messages.error(
                request,
                "Access denied."
            )

            return redirect("dashboard")

        is_admin = membership.role == User.ROLE_ADMIN
        is_creator = project.created_by == request.user
        is_uploader = document.uploaded_by == request.user

        if not (is_admin or is_creator or is_uploader):

            messages.error(
                request,
                "Only the Company Admin, Project Creator, or Document Uploader can delete this document."
            )

            return redirect(
                "project_documents",
                project_id=project.id
            )

    # --------------------------------------------------
    # Delete Document
    # --------------------------------------------------

    project_id = project.id

    if document.file:
        document.file.delete(save=False)

    document.delete()

    messages.success(
        request,
        "Document deleted successfully."
    )

    return redirect(
        "project_documents",
        project_id=project_id
    )

@login_required
@company_required
def project_activity(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    # --------------------------------------------------
    # Permission Check
    # --------------------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:

            messages.error(
                request,
                "Access denied."
            )

            return redirect("dashboard")

        # Company Admin can access every company project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(
                id=request.user.id
            ).exists():

                messages.error(
                    request,
                    "You are not authorized to view this project's activity."
                )

                return redirect("dashboard")

    # --------------------------------------------------
    # Activities
    # --------------------------------------------------

    activities = (
        project.activities
        .select_related("user")
        .order_by("-created_at")
    )

    return render(
        request,
        "projects/activity_timeline.html",
        {
            "project": project,
            "activities": activities,
            "membership": None if request.user.is_superuser else membership,
        },
    )


@login_required
@company_required
def completed_projects(request):

    # --------------------------------------------------
    # Superuser
    # --------------------------------------------------

    if request.user.is_superuser:

        projects = (
            Project.objects
            .filter(status="completed")
            .select_related("company", "created_by")
            .prefetch_related("members")
            .order_by("-created_at")
        )

    # --------------------------------------------------
    # Company Users
    # --------------------------------------------------

    else:

        company = request.current_company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # -----------------------------
        # Company Admin
        # -----------------------------

        if membership.role == User.ROLE_ADMIN:

            projects = (
                Project.objects
                .filter(
                    company=company,
                    status="completed"
                )
                .select_related("company", "created_by")
                .prefetch_related("members")
                .order_by("-created_at")
            )

        # -----------------------------
        # Normal Member
        # -----------------------------

        else:

            projects = (
                Project.objects
                .filter(
                    company=company,
                    status="completed",
                    members=request.user
                )
                .select_related("company", "created_by")
                .prefetch_related("members")
                .distinct()
                .order_by("-created_at")
            )

    return render(
        request,
        "projects/completed_projects.html",
        {
            "projects": projects,
        },
    )


@login_required
@company_required
def active_projects(request):

    # --------------------------------------------------
    # Superuser
    # --------------------------------------------------

    if request.user.is_superuser:

        projects = (
            Project.objects
            .filter(status="active")
            .select_related("company", "created_by")
            .prefetch_related("members")
            .order_by("-created_at")
        )

    # --------------------------------------------------
    # Company Users
    # --------------------------------------------------

    else:

        company = request.current_company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # -----------------------------------------
        # Company Admin
        # -----------------------------------------

        if membership.role == User.ROLE_ADMIN:

            projects = (
                Project.objects
                .filter(
                    company=company,
                    status="active"
                )
                .select_related("company", "created_by")
                .prefetch_related("members")
                .order_by("-created_at")
            )

        # -----------------------------------------
        # Normal Member
        # -----------------------------------------

        else:

            projects = (
                Project.objects
                .filter(
                    company=company,
                    status="active",
                    members=request.user
                )
                .select_related("company", "created_by")
                .prefetch_related("members")
                .distinct()
                .order_by("-created_at")
            )

    return render(
        request,
        "projects/active_projects.html",
        {
            "projects": projects,
        }
    )


@login_required
@company_required
def all_projects(request):

    # --------------------------------------------------
    # Superuser
    # --------------------------------------------------

    if request.user.is_superuser:

        projects = (
            Project.objects
            .select_related(
                "company",
                "created_by"
            )
            .prefetch_related(
                "members"
            )
            .order_by("-created_at")
        )

    # --------------------------------------------------
    # Company Users
    # --------------------------------------------------

    else:

        company = request.current_company

        membership = request.user.memberships.filter(
            company=company
        ).first()

        # -----------------------------------------
        # Company Admin
        # -----------------------------------------

        if membership.role == User.ROLE_ADMIN:

            projects = (
                Project.objects
                .filter(
                    company=company
                )
                .select_related(
                    "company",
                    "created_by"
                )
                .prefetch_related(
                    "members"
                )
                .order_by("-created_at")
            )

        # -----------------------------------------
        # Normal Member
        # -----------------------------------------

        else:

            projects = (
                Project.objects
                .filter(
                    company=company,
                    members=request.user
                )
                .select_related(
                    "company",
                    "created_by"
                )
                .prefetch_related(
                    "members"
                )
                .distinct()
                .order_by("-created_at")
            )

    return render(
        request,
        "projects/all_projects.html",
        {
            "projects": projects,
        }
    )

@login_required
@company_required
def company_project_list(request):

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
        .order_by("-created_at")
    )

    search = request.GET.get("search", "")

    if search:
        projects = projects.filter(
            Q(name__icontains=search)
        )

    can_create_projects = has_company_permission(
        request.user,
        company,
        "can_create_projects",
    )

    return render(
        request,
        "projects/company_project_list.html",
        {
            "projects": projects,
            "can_create_projects": can_create_projects,
        },
    )


@login_required
@company_required
@can_create_projects
def company_project_create(request):

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
                name__iexact=project_name,
            ).exists():

                messages.error(
                    request,
                    "A project with this name already exists.",
                )

            else:

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

                messages.success(
                    request,
                    "Project created successfully.",
                )

                return redirect("company_project_list")

    else:

        form = ProjectForm(company=company)

    return render(
        request,
        "projects/company_project_create.html",
        {
            "form": form,
            "company": company,
        },
    )

@login_required
@company_required
def company_project_detail(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
        company=request.current_company,
    )

    return render(
        request,
        "projects/company_project_detail.html",
        {
            "project": project,
        },
    )