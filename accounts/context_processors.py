from .models import Notification


def notification_context(request):

    if request.user.is_authenticated:

        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        latest_notifications = Notification.objects.filter(
            user=request.user,
        )[:5]

    else:

        unread_count = 0
        latest_notifications = []

    return {
        "unread_notifications": unread_count,
        "latest_notifications": latest_notifications,
    }



def notification_data(request):
    if request.user.is_authenticated:

        unread = Notification.objects.filter(
            user=request.user,
            is_read=False
        )

        return {
            "notification_count": unread.count(),
            "latest_notifications": unread[:5]
        }

    return {}