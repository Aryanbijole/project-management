from django.db import models
import uuid

class Project(models.Model):

    # Visibility choices
    VISIBILITY_PRIVATE = 'private'
    VISIBILITY_INTERNAL = 'internal'
    VISIBILITY_PUBLIC = 'public'

    VISIBILITY_CHOICES = [
        (VISIBILITY_PRIVATE, 'Private'),
        (VISIBILITY_INTERNAL, 'Internal'),
        (VISIBILITY_PUBLIC, 'Public'),
    ]

    # Status choices
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ON_HOLD = 'on_hold'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ON_HOLD, 'On Hold'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='projects'
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )

    # NEW FIELD
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_projects'
    )

    members = models.ManyToManyField(
        'accounts.User',
        related_name='projects',
        blank=True
    )

    # NEW FIELD
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PRIVATE
    )

    # NEW FIELD
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )

    # NEW FIELD
    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

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

class ProjectInvitation(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )

    accepted = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.email
    
class Milestone(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones'
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    due_date = models.DateField()

    completed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title   

class ProjectDocument(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    file = models.FileField(
        upload_to='project_documents/'
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return self.file.name.split("/")[-1]