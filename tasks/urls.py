from django.urls import path
from tasks import views

urlpatterns = [
    path('projects/<int:project_id>/todos/', views.todo_lists_view, name='todo_lists'),
    path('projects/<int:project_id>/todos/<int:list_id>/', views.todo_list_detail, name='todo_list_detail'),
    path('projects/<int:project_id>/todos/<int:list_id>/create-item/', views.create_todo_item, name='create_todo_item'),
    path('projects/<int:project_id>/todos/items/<int:item_id>/toggle/', views.toggle_todo_item, name='toggle_todo_item'),
    path('projects/<int:project_id>/todos/items/<int:item_id>/reassign/', views.reassign_todo_item, name='reassign_todo_item'),
]
