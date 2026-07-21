from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projects.models import Project
from integrations.models import ExternalTool
from accounts.decorators import company_required

@login_required
@company_required
def create_external_tool(request, project_id):

    # ------------------------------------------
    # Superuser
    # ------------------------------------------

    if request.user.is_superuser:

        project = get_object_or_404(
            Project,
            id=project_id
        )

    # ------------------------------------------
    # Company Users
    # ------------------------------------------

    else:

        project = get_object_or_404(
            Project,
            id=project_id,
            company=request.current_company
        )

    # ------------------------------------------
    # Only Project Owner or Company Admin
    # ------------------------------------------

    if not request.user.is_superuser:

        is_admin = CompanyMembership.objects.filter(
            company=project.company,
            user=request.user,
            role=User.ROLE_ADMIN
        ).exists()

        is_creator = (
            project.created_by == request.user
        )

        if not (is_admin or is_creator):

            messages.error(
                request,
                "Only project owners or company administrators can manage integrations."
            )

            return redirect(
                "project_detail",
                project_id=project.id
            )

    # ------------------------------------------
    # Create Integration
    # ------------------------------------------

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        url = request.POST.get("url", "").strip()

        if name and url:

            ExternalTool.objects.create(
                project=project,
                name=name,
                url=url
            )

            messages.success(
                request,
                f"External tool '{name}' integrated successfully!"
            )

        else:

            messages.error(
                request,
                "Tool name and URL are required."
            )

    return redirect(
        "project_detail",
        project_id=project.id
    )