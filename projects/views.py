from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Company, User
from projects.models import Project, ProjectTool
from integrations.models import ExternalTool
from django.views.generic import ListView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Project, Milestone, ProjectDocument
from django.core.mail import send_mail
from django.conf import settings
from .models import ProjectInvitation,ProjectDocument
from tasks.models import TodoItem
from django.db.models import Q
from accounts.models import Notification
from .forms import ProjectDocumentForm
from django.http import FileResponse

class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

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
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        company_id = request.POST.get('company_id')
        member_ids = request.POST.getlist('members')

        company = get_object_or_404(Company, id=company_id)

        if name:
            project = Project.objects.create(
                name=name,
                description=description,
                company=company,
                created_by=request.user
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
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check authorization (user must be member of project's company, or explicitly a project member)
    is_company_member = request.user.memberships.filter(company=project.company).exists()
    is_project_member = project.members.filter(id=request.user.id).exists()
    
    if not (is_company_member or is_project_member):
        messages.error(request, "You are not authorized to access this project.")
        return redirect('dashboard')

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
def add_project_member(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            project.members.add(user)
            messages.success(request, f"Added {user.email} to project members.")
        else:
            messages.error(request, "User ID not specified.")
    return redirect('project_detail', project_id=project.id)


@login_required
def configure_tools(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # User must be project creator or organization admin
    is_admin = request.user.memberships.filter(company=project.company, role=User.ROLE_ADMIN).exists()
    is_creator = (project.created_by == request.user)
    
    if not (is_admin or is_creator):
        messages.error(request, "Only project owners or administrators can configure tools.")
        return redirect('project_detail', project_id=project.id)

    tools = project.tools.all()

    if request.method == 'POST':
        for tool in tools:
            # Check if enabled check box was checked
            is_enabled = request.POST.get(f"enabled_{tool.tool_key}") == 'on'
            # Check name input
            custom_name = request.POST.get(f"name_{tool.tool_key}", tool.name).strip()
            
            tool.is_enabled = is_enabled
            if custom_name:
                tool.name = custom_name
            tool.save()
            
        messages.success(request, "Project tools configured successfully!")
        return redirect('project_detail', project_id=project.id)

    return render(request, 'projects/configure_tools.html', {
        'project': project,
        'tools': tools
    })

@login_required
def invite_project_member(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method == 'POST':

        email = request.POST.get('email')

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
            subject='Project Invitation',
            message=f'''
You have been invited to join project:
{project.name}

Open:
{invite_link}
''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(
            request,
            "Invitation email sent."
        )

    return redirect(
        'project_detail',
        project_id=project.id
    )

@login_required
def accept_invitation(request, token):

    invite = get_object_or_404(
        ProjectInvitation,
        token=token,
        accepted=False
    )

    invite.project.members.add(
        request.user
    )

    invite.accepted = True
    invite.save()

    messages.success(
        request,
        "You joined the project."
    )

    return redirect(
        'project_detail',
        project_id=invite.project.id
    )

@login_required
def add_milestone(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method == "POST":

        milestone =Milestone.objects.create(
            project=project,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            due_date=request.POST.get("due_date")
        )

        for member in project.members.all():

            if member != request.user:

                Notification.objects.create(
                    user=member,
                    title="New Milestone",
                    message=f"Milestone '{milestone.title}' was added to project '{project.name}'."
                )

        messages.success(
            request,
            "Milestone created."
        )

    return redirect(
        "project_detail",
        project_id=project.id
    )



@login_required
def analytics_dashboard(request):

    total_projects = Project.objects.count()

    total_tasks = TodoItem.objects.count()

    completed_tasks = TodoItem.objects.filter(
        status='done'
    ).count()

    pending_tasks = total_tasks - completed_tasks

    completion_percentage = 0

    if total_tasks > 0:
        completion_percentage = round(
            (completed_tasks / total_tasks) * 100,
            2
        )

    total_members = User.objects.count()

    return render(
        request,
        'projects/analytics.html',
        {
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_percentage': completion_percentage,
            'total_members': total_members,
        }
    )


@login_required
def calendar_view(request):

    tasks = TodoItem.objects.exclude(
        due_date__isnull=True
    )

    milestones = Milestone.objects.all()

    return render(
        request,
        'projects/calendar.html',
        {
            'tasks': tasks,
            'milestones': milestones,
        }
    )

@login_required
def global_search(request):

    query = request.GET.get('q', '')

    projects = Project.objects.none()
    tasks = TodoItem.objects.none()
    users = User.objects.none()
    milestones = Milestone.objects.none()

    if query:

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

    return render(
        request,
        'projects/search.html',
        {
            'query': query,
            'projects': projects,
            'tasks': tasks,
            'users': users,
            'milestones': milestones,
        }
    )

@login_required
def upload_project_document(
    request,
    project_id
):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method == "POST":

        ProjectDocument.objects.create(
            project=project,
            title=request.POST.get("title"),
            file=request.FILES["file"],
            uploaded_by=request.user
        )

    return redirect(
        "project_documents",
        project_id=project.id
    )

@login_required
def project_documents(
    request,
    project_id
):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    documents = ProjectDocument.objects.filter(
        project=project
    )

    return render(
        request,
        "projects/project_documents.html",
        {
            "project": project,
            "documents": documents
        }
    )

@login_required
def project_document_upload(request, project_id):

    project = get_object_or_404(Project, id=project_id)

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
                project.id
            )

    else:

        form = ProjectDocumentForm()

    return render(
        request,
        "projects/document_upload.html",
        {
            "project": project,
            "form": form
        }
    )

@login_required
def project_documents(request, project_id):

    project = get_object_or_404(Project, id=project_id)

    documents = ProjectDocument.objects.filter(
        project=project
    ).order_by("-uploaded_at")

    return render(
        request,
        "projects/document_list.html",
        {
            "project": project,
            "documents": documents
        }
    )

@login_required
def download_document(request, document_id):

    document = get_object_or_404(
        ProjectDocument,
        id=document_id
    )

    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.filename
    )

@login_required
def delete_document(request, document_id):

    document = get_object_or_404(
        ProjectDocument,
        id=document_id
    )

    project_id = document.project.id

    document.file.delete(save=False)
    document.delete()

    messages.success(
        request,
        "Document deleted successfully."
    )

    return redirect(
        "project_documents",
        project_id
    )