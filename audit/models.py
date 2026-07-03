from django.db import models
from django.conf import settings


class AuditLog(models.Model):

    ACTIONS = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("UPLOAD", "Upload"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    module = models.CharField(max_length=100)

    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.action} - {self.module}"
        return f"System - {self.action}"