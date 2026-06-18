from django.urls import path
from projects import views

urlpatterns = [
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/members/add/', views.add_project_member, name='add_project_member'),
    path('projects/<int:project_id>/configure/', views.configure_tools, name='configure_tools'),
]
