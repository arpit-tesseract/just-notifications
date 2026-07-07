from django.db import models
from django.conf import settings
from common.models import TimeStampMixin, SoftDeleteMixin
import uuid
# Create your models here.

class NotificationStatus(models.TextChoices):
    INITIATED = 'initiated', 'Initiated'
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'

class NotificationRecipientStatus(models.TextChoices):
    READ = 'read', 'Read'
    UNREAD = 'unread', 'Unread'
    ARCHIVED = 'archived', 'Archived'


class NotificationChannel(models.TextChoices):
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    PUSH = 'push', 'Push Notification'
    IN_APP = 'in_app', 'In App'


class NotificationCategory(TimeStampMixin):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class NotificationTemplate(TimeStampMixin):
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    icon = models.CharField(max_length=50, default='bi-info-circle-fill')
    icon_color = models.CharField(max_length=50, default='info')
    channels = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.title}"
    

class Notification(TimeStampMixin):
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, null=True, blank=True)

    title = models.CharField(max_length=255)
    content = models.TextField()
    icon = models.CharField(max_length=50, default='bi-info-circle-fill')
    icon_color = models.CharField(max_length=50, default='info')

    context_data = models.JSONField(default=dict, blank=True)

    channels = models.JSONField(default=list)
    status = models.CharField(
        max_length=50, 
        choices=NotificationStatus.choices, 
        default=NotificationStatus.PENDING,
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NotificationRecipient(TimeStampMixin, SoftDeleteMixin):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    channel = models.CharField(max_length=50, choices=NotificationChannel.choices)

    action_url = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=50, choices=NotificationRecipientStatus.choices, default=NotificationRecipientStatus.UNREAD)

    delivery_status = models.CharField(max_length=50, choices=NotificationStatus.choices, default=NotificationStatus.INITIATED)

    read_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        # CRUCIAL: Makes fetching the unread count lightning fast
        indexes = [
            models.Index(fields=['user', 'channel', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.channel} - {self.status}"


class NotificationStatusLog(TimeStampMixin):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=NotificationStatus.choices)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.notification} - {self.status}"

