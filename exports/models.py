from django.db import models

class DataExport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='exports')
    requested_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='exports')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    export_file = models.FileField(upload_to='exports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Export of {self.project.name} (Status: {self.status}) requested on {self.created_at}"
