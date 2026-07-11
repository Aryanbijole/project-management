from django.contrib import admin
from .models import Project, ProjectTool


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "owner",
        "status",
        "visibility",
        "is_archived",
    )

    list_filter = (
        "company",
        "status",
        "visibility",
        "is_archived",
    )

    search_fields = (
        "name",
        "description",
        "company__name",
        "owner__email",
    )


@admin.register(ProjectTool)
class ProjectToolAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "tool_key",
        "name",
        "is_enabled",
    )

    list_filter = (
        "is_enabled",
        "tool_key",
    )

    search_fields = (
        "tool_key",
        "name",
        "project__name",
    )

# Register your models here.
