from django.contrib import admin
from .models import (
    MessageBoardPost,
    Comment,
    PrivateMessage,
    PostAttachment,
    MessageAttachment,
    GroupMessage
)

admin.site.register(MessageBoardPost)
admin.site.register(Comment)
admin.site.register(PrivateMessage)
admin.site.register(PostAttachment)
admin.site.register(MessageAttachment)



@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):

    list_display = (
        "project",
        "group",
        "sender",
        "created_at",
    )

    search_fields = (
        "message",
        "sender__email",
        "sender__first_name",
        "sender__last_name",
    )

    list_filter = (
        "group",
        "project",
        "created_at",
    )

    ordering = ("-created_at",)
