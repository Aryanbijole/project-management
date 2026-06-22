from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from projects.models import Project
from django.utils import timezone
from .models import TimeEntry
from tasks.models import (
    TodoList,
    TodoItem,
    TodoActivity,
    ChecklistItem,
    TaskAttachment,
    TaskComment,
)
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


        priority = request.POST.get('priority', 'medium')
        status = request.POST.get('status', 'todo')
        estimated_hours = request.POST.get('estimated_hours')

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
                due_date=due_date if due_date else None,
                priority=priority,
                status=status,
                estimated_hours=estimated_hours if estimated_hours else None
            )

            # Log creation
            TodoActivity.objects.create(
                todo_item=item,
                actor=request.user,
                activity_type='created',
                description=f"Created task by {request.user.email}."
            )

            if assigned_to:

             Notification.objects.create(
             user=assigned_to,
             title='New Task Assigned',
             message=f'You were assigned task: {item.title}'
   
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

        if new_user:

         Notification.objects.create(
         user=new_user,
         title='Task Reassigned',
         message=f'You were assigned task: {item.title}'
        )
        
        messages.success(request, f"Reassigned task '{item.title}' successfully.")
        return redirect('todo_list_detail', project_id=project_id, list_id=item.todo_list.id)
        
    return redirect('project_detail', project_id=project_id)



@login_required
def task_detail(request, project_id, task_id):

    project = get_object_or_404(Project, id=project_id)

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project=project
    )

    if request.method == 'POST':

        new_status = request.POST.get('status')

        if new_status:
            task.status = new_status
            task.save()

            TodoActivity.objects.create(
                todo_item=task,
                actor=request.user,
                activity_type='status_changed',
                description=f"Changed status to {task.get_status_display()}."
            )

            messages.success(
                request,
                "Task status updated successfully."
            )

        return redirect(
            'task_detail',
            project_id=project.id,
            task_id=task.id
        )

    return render(
        request,
        'tasks/task_detail.html',
        {
            'project': project,
            'task': task,
            'comments': task.comments.all().order_by('-created_at'),
            'activities': task.activities.all().order_by('-created_at'),
            'checklist_items': task.checklist_items.all(),
            'attachments': task.attachments.all(),
            'comments': task.comments.all().order_by('-created_at'),
        }
    )


@login_required
def add_checklist_item(request, project_id, task_id):
    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id
    )

    if request.method == 'POST':
        title = request.POST.get('title')

        if title:
            ChecklistItem.objects.create(
                task=task,
                title=title
            )

    return redirect(
        'task_detail',
        project_id=project_id,
        task_id=task.id
    )

@login_required
def upload_attachment(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id
    )

    if request.method == 'POST':

        uploaded_file = request.FILES.get('file')

        if uploaded_file:

            TaskAttachment.objects.create(
                task=task,
                file=uploaded_file,
                uploaded_by=request.user
            )

            messages.success(
                request,
                "File uploaded successfully."
            )

    return redirect(
        'task_detail',
        project_id=project_id,
        task_id=task.id
    )

@login_required
def kanban_board(request, project_id):

    project = get_object_or_404(Project, id=project_id)

    todo_tasks = TodoItem.objects.filter(
        todo_list__project=project,
        status='todo'
    )

    in_progress_tasks = TodoItem.objects.filter(
        todo_list__project=project,
        status='in_progress'
    )

    review_tasks = TodoItem.objects.filter(
        todo_list__project=project,
        status='review'
    )

    done_tasks = TodoItem.objects.filter(
        todo_list__project=project,
        status='done'
    )

    return render(
        request,
        'tasks/kanban_board.html',
        {
            'project': project,
            'todo_tasks': todo_tasks,
            'in_progress_tasks': in_progress_tasks,
            'review_tasks': review_tasks,
            'done_tasks': done_tasks,
        }
    )

@login_required
def add_comment(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id
    )

    if request.method == 'POST':

        comment_text = request.POST.get('comment')

        if comment_text:

            TaskComment.objects.create(
                task=task,
                author=request.user,
                comment=comment_text
            )

    return redirect(
        'task_detail',
        project_id=project_id,
        task_id=task_id
    )

@login_required
def add_task_comment(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id
    )

    if request.method == 'POST':

        content = request.POST.get('content')

        if content:

            TaskComment.objects.create(
                task=task,
                author=request.user,
                content=content
            )

    return redirect(
        'task_detail',
        project_id=project_id,
        task_id=task.id
    )

@login_required
def start_timer(request, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id
    )

    TimeEntry.objects.create(
        task=task,
        user=request.user,
        start_time=timezone.now()
    )

    return redirect(
        'task_detail',
        project_id=task.todo_list.project.id,
        task_id=task.id
    )


@login_required
def stop_timer(request, entry_id):

    entry = get_object_or_404(
        TimeEntry,
        id=entry_id
    )

    entry.end_time = timezone.now()

    seconds = (
        entry.end_time -
        entry.start_time
    ).total_seconds()

    entry.hours = round(
        seconds / 3600,
        2
    )

    entry.save()

    return redirect(
        'task_detail',
        project_id=entry.task.todo_list.project.id,
        task_id=entry.task.id
    )