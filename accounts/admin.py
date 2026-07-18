from django.contrib import admin
from .models import (
    User,
    Company,
    CompanyMembership,
    Group,
    Invitation,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    list_filter = (
        "is_superuser",
        "is_staff",
        "is_active",
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "role",
    )

    list_filter = (
        "company",
        "role",
    )

    search_fields = (
        "user__email",
        "company__name",
    )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
    )

    search_fields = (
        "name",
        "company__name",
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "company",
        "is_accepted",
        "created_at",
    )

    list_filter = (
        "is_accepted",
        "company",
    )

    search_fields = (
        "email",
        "company__name",
    )