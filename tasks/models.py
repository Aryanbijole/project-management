from django.db import models

class TodoList(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='todo_lists')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class TodoItem(models.Model):
    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_todos')
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_todos')
    due_date = models.DateField(null=True, blank=True)
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
