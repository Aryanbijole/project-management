from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projects.models import Project
from exports.models import DataExport
from exports.services import run_project_export_async
from accounts.decorators import company_required

@login_required
@company_required
def export_list_view(request, project_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )
    exports = DataExport.objects.filter(project=project).order_by('-created_at')

    return render(request, 'exports/export_list.html', {
        'project': project,
        'exports': exports
    })


@login_required
@company_required
def request_export_view(request, project_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )

    if request.method == 'POST':
        # Create DataExport request
        data_export = DataExport.objects.create(
            project=project,
            requested_by=request.user,
            status='pending'
        )

        # Trigger async export processing
        run_project_export_async(data_export.id)

        messages.success(request, "Export request submitted! The data is being packaged in the background.")
        
    return redirect('export_list', project_id=project.id)
