from django.urls import path
from exports import views

urlpatterns = [
    path('projects/<int:project_id>/exports/', views.export_list_view, name='export_list'),
    path('projects/<int:project_id>/exports/request/', views.request_export_view, name='request_export'),
]
