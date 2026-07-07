from .models import Notification
from accounts.models import Notification


def create_notification(
    user,
    title,
    message,
    sender=None,
    notification_type=Notification.TYPE_SYSTEM,
):
    """
    Creates a notification for a user.
    """

    Notification.objects.create(
        user=user,
        sender=sender,
        title=title,
        message=message,
        notification_type=notification_type,
    )


def create_notification(user, title, message):
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )