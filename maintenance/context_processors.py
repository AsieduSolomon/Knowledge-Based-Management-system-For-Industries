from .models import Message, Notification


def unread_counts(request):
    """
    Makes unread message/notification counts available to every template
    (used by the navbar badges in base.html, which is included on every page).
    """
    if request.user.is_authenticated:
        return {
            'unread_messages_count': Message.objects.filter(
                recipient=request.user, is_read=False
            ).count(),
            'unread_notifications_count': Notification.objects.filter(
                user=request.user, is_read=False
            ).count(),
        }
    return {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
    }
