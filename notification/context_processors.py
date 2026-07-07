from notification.models import NotificationRecipient

def unread_notifications(request):
    """
    Context processor to make unread in-app notifications available to all templates.
    """
    if request.user.is_authenticated:
        # Fetch the 2 most recent notifications for the user (TESTING)
        notifications = NotificationRecipient.objects.filter(
            user_id=request.user.id,
            channel='in_app'
        ).select_related('notification').order_by('-created_at')[:10]
        
        unread_count = NotificationRecipient.objects.filter(
            user_id=request.user.id,
            status='unread',
            channel='in_app'
        ).count()
        
        return {
            'header_notifications': notifications,
            'unread_notifications_count': unread_count
        }
    return {}
