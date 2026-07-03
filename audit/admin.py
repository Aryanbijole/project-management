from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "created_at",
        "user",
        "module",
        "action",
    )

    search_fields = (
        "description",
        "module",
        "user__email",
    )

    list_filter = (
        "action",
        "module",
        "created_at",
    )