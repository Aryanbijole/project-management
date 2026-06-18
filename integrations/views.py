from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projects.models import Project
from integrations.models import ExternalTool

@login_required
def create_external_tool(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')

        if name and url:
            ExternalTool.objects.create(project=project, name=name, url=url)
            messages.success(request, f"External tool '{name}' integrated successfully!")
        else:
            messages.error(request, "Name and URL are required.")

    return redirect('project_detail', project_id=project.id)
