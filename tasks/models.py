from django.db import models
class TodoList(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='todo_lists')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class TodoItem(models.Model):

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
   
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )

    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_REVIEW = 'review'
    STATUS_DONE = 'done'

    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_REVIEW, 'Review'),
        (STATUS_DONE, 'Done'),
]
    
    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default=STATUS_TODO
)
    is_completed = models.BooleanField(default=False)

    
    

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_todos')
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_todos')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    null=True,
    blank=True
)
    
    is_recurring = models.BooleanField(
    default=False
    )

    repeat_days = models.PositiveIntegerField(
    null=True,
    blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def reassign(self, new_user, actor=None):
        old_user = self.assigned_to
        self.assigned_to = new_user
        self.save()
        
        # Log reassignment activity
        actor_name = actor.email if actor else "System"
        from_name = old_user.email if old_user else "Unassigned"
        to_name = new_user.email if new_user else "Unassigned"
        
        TodoActivity.objects.create(
            todo_item=self,
            actor=actor,
            activity_type='reassigned',
            description=f"Reassigned from {from_name} to {to_name} by {actor_name}."
        )


class TodoActivity(models.Model):
    todo_item = models.ForeignKey(TodoItem, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    activity_type = models.CharField(max_length=50) # e.g. 'created', 'completed', 'reassigned'
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.todo_item.title}: {self.description}"
    
class TaskAttachment(models.Model):
    task = models.ForeignKey(
        TodoItem,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(
        upload_to='task_attachments/'
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file.name

class ChecklistItem(models.Model):
    task = models.ForeignKey(
        TodoItem,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )

    title = models.CharField(max_length=255)

    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title   

class TaskComment(models.Model):

    task = models.ForeignKey(
        TodoItem,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )

    content  = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.author.email}"         

class TimeEntry(models.Model):

    task = models.ForeignKey(
        TodoItem,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.task.title}"
    
class TimeEntry(models.Model):

    task = models.ForeignKey(
        TodoItem,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )

    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    note = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.email} - {self.hours}h"    