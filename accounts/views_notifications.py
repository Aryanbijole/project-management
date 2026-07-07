from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Notification


@login_required
def notification_list(request):

    notifications = Notification.objects.filter(
        user=request.user
    )

    return render(
        request,
        "accounts/notifications.html",
        {
            "notifications": notifications
        },
    )


@login_required
def mark_notification_read(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user,
    )

    notification.is_read = True
    notification.save()

    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(is_read=True)

    return redirect("notifications")