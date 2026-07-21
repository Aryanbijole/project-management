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
from accounts.models import Notification
from decimal import Decimal
from projects.models import ProjectActivity
from accounts.decorators import company_required











from .forms import (
    TodoListForm,
    TodoItemForm,
    ChecklistItemForm,
    TaskCommentForm,
    TaskAttachmentForm,
    TimeEntryForm,
)


@login_required
@company_required
def todo_lists_view(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User is not part of this company
        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        # Company Admin -> all projects
        if membership.role != User.ROLE_ADMIN:

            # Members -> only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this project."
                )
                return redirect("dashboard")

    # -----------------------------------------

    lists = TodoList.objects.filter(project=project)

    if request.method == "POST":

        name = request.POST.get("name")

        if name:

            TodoList.objects.create(
                project=project,
                name=name,
            )

            messages.success(
                request,
                f"Todo list '{name}' created successfully!"
            )

            return redirect(
                "todo_lists",
                project_id=project.id,
            )

        messages.error(
            request,
            "Todo list name is required."
        )

    return render(
        request,
        "tasks/todo_lists.html",
        {
            "project": project,
            "lists": lists,
        },
    )


@login_required
@company_required
def todo_list_detail(request, project_id, list_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User not in this company
        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        # Company Admin -> access every project
        if membership.role != User.ROLE_ADMIN:

            # Members -> only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this project."
                )
                return redirect("dashboard")

    # -----------------------------------------

    todo_list = get_object_or_404(
        TodoList,
        id=list_id,
        project=project,
    )

    items = todo_list.items.all()

    project_members = project.members.all()

    return render(
        request,
        "tasks/todo_list_detail.html",
        {
            "project": project,
            "todo_list": todo_list,
            "items": items,
            "project_members": project_members,
        },
    )

@login_required
@company_required
def create_todo_item(request, project_id, list_id):
    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        if membership.role != User.ROLE_ADMIN:

            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this project."
                )
                return redirect("dashboard")
        


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
                assigned_to = get_object_or_404(
                    User,
                    id=assigned_to_id,
                    memberships__company=project.company
                )

            item = TodoItem.objects.create(
                todo_list=todo_list,
                title=title,
                description=description,
                assigned_to=assigned_to,
                created_by=request.user,
                due_date=due_date if due_date else None,
                priority=priority,
                status=status,
                estimated_hours=estimated_hours if estimated_hours else None,
                is_recurring='is_recurring' in request.POST,
                repeat_days=int(request.POST.get("repeat_days")) if request.POST.get("repeat_days") else None,
            )

            ProjectActivity.objects.create(
              project=todo_list.project,
              user=request.user,
              action="Task Created",
              description=f"Created task '{item.title}'."
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
@company_required
def toggle_todo_item(request, project_id, item_id):
    item = get_object_or_404(
        TodoItem,
        id=item_id,
        todo_list__project_id=project_id,
    )

    project = item.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        if not membership:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Access denied."
                },
                status=403,
            )

        if membership.role != User.ROLE_ADMIN:

            if not project.members.filter(id=request.user.id).exists():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Access denied."
                    },
                    status=403,
                )
        

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
@company_required
def reassign_todo_item(request, project_id, item_id):
    item = get_object_or_404(
        TodoItem,
        id=item_id,
        todo_list__project_id=project_id,
    )

    project = item.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
             company=project.company
        ).first()

        if not membership:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

        if membership.role != User.ROLE_ADMIN:

            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this project."
                )
                return redirect("dashboard")
        

    
    if request.method == 'POST':

        # -----------------------------------------
        # Reassignment Permission
        # -----------------------------------------

        if not request.user.is_superuser:
    
            # Company Admin can reassign any company task
            if membership.role != User.ROLE_ADMIN:

                # Only the creator of the task may reassign it
                if item.created_by != request.user:

                    messages.error(
                        request,
                        "Only the task creator or the Company Admin can reassign this task."
                    )

                    return redirect(
                        "todo_list_detail",
                        project_id=project.id,
                        list_id=item.todo_list.id,
                    )        
            
        assigned_to_id = request.POST.get('assigned_to')
        new_user = None
        if assigned_to_id:
            new_user = get_object_or_404(
                User,
                id=assigned_to_id,
                memberships__company=project.company
            )
            
        item.reassign(new_user, actor=request.user)

        ProjectActivity.objects.create(
            project=item.todo_list.project,
            user=request.user,
            action="Task Reassigned",
            description=f"Reassigned '{item.title}' to {new_user.get_full_name() or new_user.username}."
        )

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
@company_required
def task_detail(request, project_id, task_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                 request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this task."
                )
                return redirect("dashboard")

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project=project
    )

    time_entries = TimeEntry.objects.filter(
        task=task
    ).order_by('-created_at')

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
    
    running_timer = TimeEntry.objects.filter(
    task=task,
    user=request.user,
    end_time__isnull=True,
    is_manual=False
     ).first()

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
            'time_entries': time_entries,
            'running_timer': running_timer,
        }
    )

@login_required
@company_required
def add_checklist_item(request, project_id, task_id):
    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id,
    )

    project = task.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to modify this task."
                )
                return redirect("dashboard")
        
    
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
@company_required
def upload_attachment(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id,
    )

    project = task.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to upload files to this task."
                )
                return redirect("dashboard")

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
@company_required
def kanban_board(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this Kanban board."
                )
                return redirect("dashboard")
        

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
@company_required
def add_comment(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id,
    )

    project = task.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to comment on this task."
                )
                return redirect("dashboard")
        
    if request.method == 'POST':

        comment_text = request.POST.get('comment')

        if comment_text:

            TaskComment.objects.create(
                task=task,
                author=request.user,
                content=comment_text
            )

            Notification.objects.create(
            user=task.created_by,
            title="New Task Comment",
            message=f"{request.user.email} commented on task '{task.title}'."
            )

    return redirect(
        'task_detail',
        project_id=project_id,
        task_id=task_id
    )

@login_required
@company_required
def add_task_comment(request, project_id, task_id):
    task = get_object_or_404(
        TodoItem,
        id=task_id,
       todo_list__project_id=project_id,
    )

    project = task.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to comment on this task."
                )
                return redirect("dashboard")

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
@company_required
def start_timer(request, project_id, task_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project=project,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
               "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this task."
                )
                return redirect("dashboard")

    running = TimeEntry.objects.filter(
    task=task,
    user=request.user,
    end_time__isnull=True,
    start_time__isnull=False,
    is_manual=False
    ).first()  


    if not running:

        TimeEntry.objects.create(
            task=task,
            user=request.user,
            start_time=timezone.now(),
            is_manual=False
        )

        messages.success(request, "Timer started.")

    else:

        messages.warning(request, "A timer is already running.")

    return redirect(
        "task_detail",
        project_id=project.id,
        task_id=task.id
    )


@login_required
@company_required
def stop_timer(request, project_id, task_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project=project,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this task."
                )
                return redirect("dashboard")

    timer = TimeEntry.objects.filter(
        task=task,
        user=request.user,
        end_time__isnull=True,
        start_time__isnull=False,
        is_manual=False
    ).first()

    if not timer or not timer.start_time:
        messages.error(request, "No active timer found.")
        return redirect(
            "task_detail",
            project_id=project.id,
            task_id=task.id
        )

    timer.end_time = timezone.now()

    seconds = (timer.end_time - timer.start_time).total_seconds()

    timer.hours = round(
        Decimal(seconds / 3600),
        2
    )

    timer.save()

    messages.success(request, "Timer stopped successfully.")

    return redirect(
        "task_detail",
        project_id=project.id,
        task_id=task.id
    )


@login_required
@company_required
def log_time(request, project_id, task_id):

    task = get_object_or_404(
        TodoItem,
        id=task_id,
        todo_list__project_id=project_id,
    )

    project = task.todo_list.project

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to log time for this task."
                )
                return redirect("dashboard")

    if request.method == "POST":

        TimeEntry.objects.create(
            task=task,
            user=request.user,
            hours=request.POST.get("hours"),
            note=request.POST.get("note")
        )

    return redirect(
        "task_detail",
        project_id=project_id,
        task_id=task.id
    )

@login_required
@company_required
def gantt_view(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this Gantt chart."
                )
                return redirect("dashboard")
        

    tasks = TodoItem.objects.filter(
        todo_list__project=project
    ).order_by("due_date")

    return render(
        request,
        "tasks/gantt.html",
        {
            "project": project,
            "tasks": tasks,
        }
    )

@login_required
@company_required
def all_tasks(request):

    if request.user.is_superuser:

        tasks = TodoItem.objects.select_related(
            "todo_list",
            "assigned_to",
        )

    else:

        membership = request.user.memberships.first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        if membership.role == User.ROLE_ADMIN:

            tasks = TodoItem.objects.filter(
                todo_list__project__company=membership.company
            ).select_related(
                "todo_list",
                "assigned_to",
            )

        else:

            tasks = TodoItem.objects.filter(
                todo_list__project__members=request.user
            ).distinct().select_related(
                "todo_list",
                "assigned_to",
            )

    return render(
        request,
        "tasks/all_tasks.html",
        {
            "tasks": tasks,
            "title": "All Tasks"
        }
    )


@login_required
@company_required
def pending_tasks(request):

    if request.user.is_superuser:

        tasks = TodoItem.objects.exclude(
            status="done"
        ).select_related(
            "todo_list",
            "assigned_to",
        )

    else:

        membership = request.user.memberships.first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        if membership.role == User.ROLE_ADMIN:

            tasks = TodoItem.objects.filter(
                todo_list__project__company=membership.company
            ).exclude(
                status="done"
            ).select_related(
                "todo_list",
                "assigned_to",
            )

        else:

            tasks = TodoItem.objects.filter(
                todo_list__project__members=request.user
            ).exclude(
                status="done"
            ).distinct().select_related(
                "todo_list",
               "assigned_to",
            )



    return render(
        request,
        "tasks/all_tasks.html",
        {
            "tasks": tasks,
            "title": "Pending Tasks"
        }
    )


@login_required
@company_required
def completed_tasks(request):

    if request.user.is_superuser:

        tasks = TodoItem.objects.filter(
            status="done"
        ).select_related(
            "todo_list",
            "assigned_to",
        )

    else:

        membership = request.user.memberships.first()

        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        if membership.role == User.ROLE_ADMIN:

            tasks = TodoItem.objects.filter(
                todo_list__project__company=membership.company,
                status="done"
            ).select_related(
                "todo_list",
                "assigned_to",
            )

        else:

            tasks = TodoItem.objects.filter(
                todo_list__project__members=request.user,
                status="done"
            ).distinct().select_related(
                "todo_list",
                "assigned_to",
            )

    return render(
        request,
        "tasks/all_tasks.html",
        {
            "tasks": tasks,
            "title": "Completed Tasks"
        }
    )