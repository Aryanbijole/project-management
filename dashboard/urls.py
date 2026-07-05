from django.urls import path
from . import views

urlpatterns = [
    path(
    "reports/",
    views.admin_reports,
    name="admin_reports",
    ),
    path("users/", views.user_list, name="admin_users"),

    path(
    "users/create/",
    views.user_create,
    name="admin_user_create"
),

path(
    "users/<int:user_id>/edit/",
    views.user_edit,
    name="admin_user_edit"
),

path(
    "users/<int:user_id>/delete/",
    views.user_delete,
    name="admin_user_delete"
),

# Admin
path(
    "admin/projects/",
    views.project_list,
    name="admin_project_list",
),



path(
    "projects/create/",
    views.project_create,
    name="admin_project_create",
),

path(
    "projects/<int:project_id>/edit/",
    views.project_edit,
    name="admin_project_edit",
),

path(
    "projects/<int:project_id>/delete/",
    views.project_delete,
    name="admin_project_delete",
),

path(
    "companies/",
    views.company_list,
    name="admin_company_list",
),

path(
    "companies/create/",
    views.company_create,
    name="admin_company_create",
),

path(
    "companies/<int:company_id>/edit/",
    views.company_edit,
    name="admin_company_edit",
),

path(
    "companies/<int:company_id>/delete/",
    views.company_delete,
    name="admin_company_delete",
),

path(
    "groups/",
    views.group_list,
    name="admin_group_list",
),

path(
    "groups/create/",
    views.group_create,
    name="admin_group_create",
),

path(
    "groups/<int:group_id>/edit/",
    views.group_edit,
    name="admin_group_edit",
),

path(
    "groups/<int:group_id>/delete/",
    views.group_delete,
    name="admin_group_delete",
),

path(
    "admin/groups/<int:group_id>/",
    views.group_detail,
    name="admin_group_detail",
),

path(
    "groups/<int:group_id>/remove/<int:user_id>/",
    views.remove_group_member,
    name="remove_group_member",
),

path(
    "organization/members/",
    views.organization_members,
    name="organization_members",
),

path(
    "organization/members/<int:membership_id>/edit/",
    views.organization_member_edit,
    name="organization_member_edit",
),

path(
    "organization/members/<int:membership_id>/delete/",
    views.organization_member_delete,
    name="organization_member_delete",
),

# Role Management
path(
    "roles/",
    views.role_list,
    name="admin_role_list",
),

path(
    "roles/create/",
    views.role_create,
    name="admin_role_create",
),

path(
    "roles/<int:role_id>/edit/",
    views.role_edit,
    name="admin_role_edit",
),

path(
    "roles/<int:role_id>/delete/",
    views.role_delete,
    name="admin_role_delete",
),

path(
    "audit-logs/",
    views.audit_logs,
    name="admin_audit_logs",
),

path(
    "admin/projects/<int:project_id>/",
    views.project_detail,
    name="admin_project_detail",
),

path(
    "admin/projects/archived/",
    views.archived_projects,
    name="admin_archived_projects",
),

path(
   "admin/projects/<int:project_id>/archive/",
   views.project_archive,
   name="admin_project_archive", 
 ),

path(
    "projects/<int:project_id>/restore/",
    views.restore_project,
    name="admin_project_restore",
),

path(
    "projects/",
    views.user_project_list,
    name="project_list",
),
]
