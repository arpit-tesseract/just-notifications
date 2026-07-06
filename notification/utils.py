from .models import (
    Notification,
    NotificationRecipient,
    NotificationChannel,
    NotificationStatus,
    NotificationQueue,
    NotificationCategory,
    NotificationPriority,
    NotificationTemplate
)

def send_system_notification(users, title=None, message=None, template_code=None, metadata=None):
    """
    Creates a system notification and queues it for the given users.
    Triggers WebSockets automatically via post_save signal on NotificationRecipient.
    """
    if metadata is None:
        metadata = {}

    template_obj = None
    category = None
    priority = None
    
    if template_code:
        template_obj = NotificationTemplate.objects.filter(code=template_code, is_active=True).first()
        if template_obj:
            try:
                title = template_obj.title.format(**metadata)
                message = template_obj.body.format(**metadata)
                category = template_obj.category
                priority = template_obj.priority
            except KeyError:
                pass 

    if not title or not message:
        return None

    # Fallback to first available category/priority if None
    if not category:
        category = NotificationCategory.objects.first()
    if not priority:
        priority = NotificationPriority.objects.first()

    notification = Notification.objects.create(
        title=title,
        message=message,
        category=category,
        priority=priority,
        metadata=metadata,
        is_system_generated=True,
        template=template_obj
    )

    for user in users:
        NotificationRecipient.objects.get_or_create(notification=notification, user=user)

    channels = NotificationChannel.objects.filter(code__in=['email', 'in-app'], is_active=True)
    status_obj = NotificationStatus.objects.filter(is_default=True, is_active=True).first()

    if status_obj and channels.exists():
        for user in users:
            for channel in channels:
                NotificationQueue.objects.get_or_create(
                    notification=notification,
                    recipient=user,
                    channel=channel,
                    status=status_obj
                )
    
    return notification
