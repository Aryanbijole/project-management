from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projects.models import Project
from integrations.models import ExternalTool
from accounts.decorators import company_required

@login_required
@company_required
def create_external_tool(request, project_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )

    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')

        if name and url:
            ExternalTool.objects.create(project=project, name=name, url=url)
            messages.success(request, f"External tool '{name}' integrated successfully!")
        else:
            messages.error(request, "Name and URL are required.")

    return redirect('project_detail', project_id=project.id)
