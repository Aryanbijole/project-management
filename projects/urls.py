from django.urls import path
from projects import views
from .views import ProjectListView, ProjectCreateView

urlpatterns = [

    # Project List Page
    path(
    '',
    ProjectListView.as_view(),
    name='project-list'
    ),

    # New Project Form Page
    path(
        'new/',
        ProjectCreateView.as_view(),
        name='project-create'
    ),

    # Existing Project Functions
    path(
        'create/',
        views.create_project,
        name='create_project'
    ),

    path(
        '<int:project_id>/',
        views.project_detail,
        name='project_detail'
    ),

    path(
        '<int:project_id>/members/add/',
        views.add_project_member,
        name='add_project_member'
    ),

    path(
        '<int:project_id>/configure/',
        views.configure_tools,
        name='configure_tools'
    ),

    path(
    '<int:project_id>/invite/',
    views.invite_project_member,
    name='invite_project_member'
),

path(
    'invitations/<uuid:token>/',
    views.accept_invitation,
    name='accept_invitation'
),

path(
    '<int:project_id>/milestone/add/',
    views.add_milestone,
    name='add_milestone'
),

path(
    'analytics/',
    views.analytics_dashboard,
    name='analytics_dashboard'
),

path(
    'calendar/',
    views.calendar_view,
    name='calendar_view'
),

path(
    'search/',
    views.global_search,
    name='global_search'
),

path(
    'projects/<int:project_id>/documents/',
    views.project_documents,
    name='project_documents'
),

path(
    'projects/<int:project_id>/documents/upload/',
    views.project_document_upload,
    name="project_document_upload",
),


path(
    "documents/<int:document_id>/download/",
    views.download_document,
    name="download_document",
),

path(
    "documents/<int:document_id>/delete/",
    views.delete_document,
    name="delete_document",
),

path(
    "<int:project_id>/activity/",
    views.project_activity,
    name="project_activity"
),

path(
    "summary/all/",
    views.all_projects,
    name="all_projects"
),

path(
    "summary/active/",
    views.active_projects,
    name="active_projects"
),

path(
    "summary/completed/",
    views.completed_projects,
    name="completed_projects"
),


path(
    "company/projects/",
    views.company_project_list,
    name="company_project_list",
),

path(
    "company/projects/create/",
    views.company_project_create,
    name="company_project_create",
),

path(
    "company/projects/<int:project_id>/",
    views.company_project_detail,
    name="company_project_detail",
),

]