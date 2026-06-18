from django.db import models

class ExternalTool(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='external_tools')
    name = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} in {self.project.name} ({self.url})"
