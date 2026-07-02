from django.db import models
from ckeditor.fields import RichTextField

class MessageBoardPost(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = RichTextField()
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author.email if self.author else 'Unknown'}"


class Comment(models.Model):
    post = models.ForeignKey(MessageBoardPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    mentioned_users = models.ManyToManyField(
    'accounts.User',
    blank=True,
    related_name='mentions'
)
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.email if self.author else 'Unknown'} on {self.post.title}"

class PostAttachment(models.Model):
    post = models.ForeignKey(
        MessageBoardPost,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(
        upload_to='post_attachments/'
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

class PrivateMessage(models.Model):
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email} at {self.created_at}"
    
class MessageAttachment(models.Model):
    message = models.ForeignKey(
        PrivateMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(
        upload_to='message_attachments/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file.name    


