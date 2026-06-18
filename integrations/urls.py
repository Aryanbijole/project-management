from django.urls import path
from integrations import views

urlpatterns = [
    path('projects/<int:project_id>/integrations/create/', views.create_external_tool, name='create_external_tool'),
]
