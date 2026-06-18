from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Company, User
from projects.models import Project, ProjectTool
from integrations.models import ExternalTool

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

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'tools': tools,
        'enabled_keys': enabled_keys,
        'tool_names': tool_names,
        'external_tools': external_tools,
        'company_users': company_users,
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
