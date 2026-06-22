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
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='groups')
    members = models.ManyToManyField(User, related_name='custom_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Invitation(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invitations')
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.email} to {self.company.name} as {self.role}"

class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title