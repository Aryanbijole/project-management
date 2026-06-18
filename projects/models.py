from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_projects')
    members = models.ManyToManyField('accounts.User', related_name='projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Create default tools when project is initialized
            # Changes to defaults below will apply only to new projects.
            from django.conf import settings
            default_tools = getattr(settings, 'DEFAULT_PROJECT_TOOLS', {
                'todo': 'To-Do Lists',
                'message_board': 'Message Board',
                'chat': 'Private Pings',
                'integrations': 'External Tools',
            })
            for key, name in default_tools.items():
                ProjectTool.objects.create(
                    project=self,
                    tool_key=key,
                    name=name,
                    is_enabled=True
                )


class ProjectTool(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tools')
    tool_key = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'tool_key')

    def __str__(self):
        return f"{self.name} in {self.project.name} ({'Enabled' if self.is_enabled else 'Disabled'})"
