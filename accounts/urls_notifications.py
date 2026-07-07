from django.urls import path
from . import views_notifications

urlpatterns = [
    path(
        "",
        views_notifications.notification_list,
        name="notifications",
    ),

    path(
        "<int:notification_id>/read/",
        views_notifications.mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "mark-all-read/",
        views_notifications.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
]