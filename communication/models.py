from django.db import models

class MessageBoardPost(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField() # Rich content written in Markdown
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author.email if self.author else 'Unknown'}"


class Comment(models.Model):
    post = models.ForeignKey(MessageBoardPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.email if self.author else 'Unknown'} on {self.post.title}"


class PrivateMessage(models.Model):
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email} at {self.created_at}"
