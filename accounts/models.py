from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import uuid

class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CLIENT = 'client'
    ROLE_COLLABORATOR = 'collaborator'

   
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Organization Member'),
        (ROLE_CLIENT, 'Client'),
        (ROLE_COLLABORATOR, 'Outside Collaborator'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
    )

    custom_role = models.ForeignKey(
        "Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_merged = models.BooleanField(default=False)
    merged_into = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_accounts')

    # Use email as primary username/login identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(
    max_length=255,
    unique=True,
    blank=True
)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompanyMembership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.company.name} as {self.role}"


class Group(models.Model):
    name = models.CharField(max_length=255)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="groups"
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="groups",
        null=True,
        blank=True,
    )

    members = models.ManyToManyField(
        User,
        related_name="custom_groups",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    
class Role(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="roles",
        
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    
    
    
    
    can_create_projects = models.BooleanField(default=False)
    can_edit_projects = models.BooleanField(default=False)
    

    can_create_tasks = models.BooleanField(default=False)
    can_edit_tasks = models.BooleanField(default=False)
    

    can_upload_files = models.BooleanField(default=False)

    can_view_reports = models.BooleanField(default=False)

    can_invite_members = models.BooleanField(default=False)

    can_view_audit_logs = models.BooleanField(default=False)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Invitation(models.Model):
    email = models.EmailField()
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invitations')
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.email} to {self.company.name} as {self.role}"

class Notification(models.Model):

    TYPE_TASK = "task"
    TYPE_PROJECT = "project"
    TYPE_COMMENT = "comment"
    TYPE_SYSTEM = "system"

    TYPE_CHOICES = [
        (TYPE_TASK, "Task"),
        (TYPE_PROJECT, "Project"),
        (TYPE_COMMENT, "Comment"),
        (TYPE_SYSTEM, "System"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_SYSTEM
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    
