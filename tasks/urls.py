from django.urls import path
from tasks import views

urlpatterns = [
    path('projects/<int:project_id>/todos/', views.todo_lists_view, name='todo_lists'),
    path('projects/<int:project_id>/todos/<int:list_id>/', views.todo_list_detail, name='todo_list_detail'),
    path('projects/<int:project_id>/todos/<int:list_id>/create-item/', views.create_todo_item, name='create_todo_item'),
    path('projects/<int:project_id>/todos/items/<int:item_id>/toggle/', views.toggle_todo_item, name='toggle_todo_item'),
    path('projects/<int:project_id>/todos/items/<int:item_id>/reassign/', views.reassign_todo_item, name='reassign_todo_item'),

   
    path(
    'projects/<int:project_id>/tasks/<int:task_id>/',
    views.task_detail,
    name='task_detail'
),

path(
    'projects/<int:project_id>/tasks/<int:task_id>/add-checklist/',
    views.add_checklist_item,
    name='add_checklist_item'
),

path(
    'projects/<int:project_id>/tasks/<int:task_id>/upload/',
    views.upload_attachment,
    name='upload_attachment'
),

path(
    'projects/<int:project_id>/kanban/',
    views.kanban_board,
    name='kanban_board'
),

path(
    'projects/<int:project_id>/tasks/<int:task_id>/add-checklist/',
    views.add_checklist_item,
    name='add_checklist_item'
), 

path(
    'projects/<int:project_id>/tasks/<int:task_id>/comment/',
    views.add_comment,
    name='task_add_comment'
),

path(
    'projects/<int:project_id>/tasks/<int:task_id>/comment/',
    views.add_task_comment,
    name='add_task_comment'
),

path(
    'timer/start/<int:task_id>/',
    views.start_timer,
    name='start_timer'
),

path(
    'timer/stop/<int:entry_id>/',
    views.stop_timer,
    name='stop_timer'
),
]
