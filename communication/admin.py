from django.contrib import admin
from .models import (
    MessageBoardPost,
    Comment,
    PrivateMessage,
    PostAttachment,
    MessageAttachment
)

admin.site.register(MessageBoardPost)
admin.site.register(Comment)
admin.site.register(PrivateMessage)
admin.site.register(PostAttachment)
admin.site.register(MessageAttachment)
