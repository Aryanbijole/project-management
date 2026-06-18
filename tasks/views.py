from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from projects.models import Project
from tasks.models import TodoList, TodoItem, TodoActivity
from accounts.models import User

@login_required
def todo_lists_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    lists = TodoList.objects.filter(project=project)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            TodoList.objects.create(project=project, name=name)
            messages.success(request, f"Todo list '{name}' created successfully!")
            return redirect('todo_lists', project_id=project.id)
        else:
            messages.error(request, "Todo list name is required.")
            
    return render(request, 'tasks/todo_lists.html', {
        'project': project,
        'lists': lists
    })


@login_required
def todo_list_detail(request, project_id, list_id):
    project = get_object_or_404(Project, id=project_id)
    todo_list = get_object_or_404(TodoList, id=list_id, project=project)
    items = todo_list.items.all()
    project_members = project.members.all()

    return render(request, 'tasks/todo_list_detail.html', {
        'project': project,
        'todo_list': todo_list,
        'items': items,
        'project_members': project_members
    })


@login_required
def create_todo_item(request, project_id, list_id):
    project = get_object_or_404(Project, id=project_id)
    todo_list = get_object_or_404(TodoList, id=list_id, project=project)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')

        if title:
            assigned_to = None
            if assigned_to_id:
                assigned_to = get_object_or_404(User, id=assigned_to_id)

            item = TodoItem.objects.create(
                todo_list=todo_list,
                title=title,
                description=description,
                assigned_to=assigned_to,
                created_by=request.user,
                due_date=due_date if due_date else None
            )

            # Log creation
            TodoActivity.objects.create(
                todo_item=item,
                actor=request.user,
                activity_type='created',
                description=f"Created task by {request.user.email}."
            )

            messages.success(request, f"Task '{title}' created!")
        else:
            messages.error(request, "Task title is required.")

    return redirect('todo_list_detail', project_id=project.id, list_id=todo_list.id)


@login_required
def toggle_todo_item(request, project_id, item_id):
    item = get_object_or_404(TodoItem, id=item_id, todo_list__project_id=project_id)
    
    if request.method == 'POST':
        item.is_completed = not item.is_completed
        item.save()

        # Log completion activity
        status_text = "completed" if item.is_completed else "reopened"
        TodoActivity.objects.create(
            todo_item=item,
            actor=request.user,
            activity_type='toggle',
            description=f"Marked as {status_text} by {request.user.email}."
        )

        return JsonResponse({
            'status': 'success',
            'is_completed': item.is_completed
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def reassign_todo_item(request, project_id, item_id):
    item = get_object_or_404(TodoItem, id=item_id, todo_list__project_id=project_id)
    
    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to')
        new_user = None
        if assigned_to_id:
            new_user = get_object_or_404(User, id=assigned_to_id)
            
        item.reassign(new_user, actor=request.user)
        
        messages.success(request, f"Reassigned task '{item.title}' successfully.")
        return redirect('todo_list_detail', project_id=project_id, list_id=item.todo_list.id)
        
    return redirect('project_detail', project_id=project_id)
