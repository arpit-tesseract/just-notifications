from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import AuditMixin, SoftDeleteMixin


'''class NotificationType(models.TextChoices):
    SYSTEM = "SYSTEM", _("System")
    USER = "USER", _("User")
    PRODUCT = "PRODUCT", _("Product")
    ORDER = "ORDER", _("Order")
    PAYMENT = "PAYMENT", _("Payment")
    INVENTORY = "INVENTORY", _("Inventory")
    PROFILE = "PROFILE", _("Profile")
    SECURITY = "SECURITY", _("Security")
    GENERAL = "GENERAL", _("General")'''


class NotificationPriority(AuditMixin, SoftDeleteMixin):
    """
    Master table for notification priorities.

    Examples:
    - Critical
    - High
    - Medium
    - Low
    - Info
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name."
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Backend identifier."
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Color shown in UI."
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frontend icon."
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "notification_priorities"

        ordering = [
            "display_order",
        ]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

class NotificationCategory(AuditMixin, SoftDeleteMixin):
    """
    Master table for notification categories.

    Examples:
    - Order
    - Payment
    - Product
    - Inventory
    - Security
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "notification_categories"

        ordering = ["name"]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name    

class NotificationTemplate(AuditMixin):
    """
    Stores reusable notification templates.

    Example:
        Code : ORDER_CREATED

        Title :
            Order Created

        Body :
            Order #{order_id} has been placed successfully.
    """

    category = models.ForeignKey(
    NotificationCategory,
    on_delete=models.PROTECT,
    related_name="templates",
)
    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
    )

    body = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "notification_templates"

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.code
    
from user.models import User
class Notification(AuditMixin, SoftDeleteMixin):
    """
    Actual notification generated from a template.

    Example:
        Title :
            Order Created

        Message :
            Order #125 created successfully.

        Action URL :
            /orders/125/

    One notification can be sent to many users.
    """

    category = models.ForeignKey(
    NotificationCategory,
    on_delete=models.PROTECT,
    related_name="notifications",
)
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    is_system_generated = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "notifications"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_deleted"]),
        ]

    def __str__(self):
        return self.title
    

class NotificationRecipient(AuditMixin, SoftDeleteMixin):
    """
    Stores notification status for every user.

    One Notification
            ↓
    Many Users

    Every user has their own
    - Read status
    - Seen status
    - Archived status
    - Deleted status
    """

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    is_seen = models.BooleanField(
        default=False,
    )

    seen_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    archived_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:

        db_table = "notification_recipients"

        ordering = [
            "-created_at"
        ]

        unique_together = (
            "notification",
            "user",
        )

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["notification"]),
            models.Index(fields=["is_seen"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["is_archived"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
    

#user to control how they receive notifications
class NotificationPreference(AuditMixin):
    """
    Stores notification preferences for each user.

    Every user has exactly one preference record.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )

    in_app = models.BooleanField(
        default=True,
        help_text="Receive notifications inside the application.",
    )

    email = models.BooleanField(
        default=True,
        help_text="Receive notifications through email.",
    )

    '''push = models.BooleanField(
        default=True,
        help_text="Receive push notifications.",
    )'''

    '''sms = models.BooleanField(
        default=False,
        help_text="Receive SMS notifications.",
    )'''

    enabled_categories = models.ManyToManyField(
        NotificationCategory,
        blank=True,
        related_name="preferences",
    )

    class Meta:
        db_table = "notification_preferences"

        ordering = [
            "user"
        ]

    def __str__(self):
        return f"{self.user.username}"
    

class NotificationAttachment(AuditMixin, SoftDeleteMixin):
    """
    Stores files attached to notifications.

    Examples:
    - Invoice PDF
    - Product Image
    - Payment Receipt
    - Offer Banner
    """

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="notifications/",
    )

    file_name = models.CharField(
        max_length=255,
    )

    file_type = models.CharField(
        max_length=100,
    )

    file_size = models.BigIntegerField()

    class Meta:
        db_table = "notification_attachments"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(fields=["notification"]),
        ]

    def __str__(self):
        return self.file_name
    

class NotificationChannel(AuditMixin, SoftDeleteMixin):
    """
    Master table for notification delivery channels.

    Examples:
    - In App
    - Email
    - Push
    - SMS
    - WhatsApp
    - Slack
    - Webhook
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name."
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Backend identifier."
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frontend icon."
    )

    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "notification_channels"

        ordering = [
            "display_order",
            "name",
        ]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name
    

class NotificationStatus(AuditMixin, SoftDeleteMixin):
    """
    Master table for notification delivery statuses.

    Examples:
    - Pending
    - Processing
    - Sent
    - Delivered
    - Failed
    - Retrying
    - Cancelled
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name."
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique backend code."
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="UI badge color."
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frontend icon."
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    is_final = models.BooleanField(
        default=False,
        help_text="Whether this status is terminal."
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "notification_statuses"

        ordering = [
            "display_order",
            "name",
        ]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_final"]),
        ]

    def __str__(self):
        return self.name
    
from django.db import models

from common.models import AuditMixin
from user.models import User

from .models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)


class NotificationQueue(AuditMixin):
    """
    Queue table.

    Every notification delivery request first enters this table.

    Celery workers continuously process pending records.
    """

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="queue_items",
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_queue",
    )

    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.PROTECT,
        related_name="queue_items",
    )

    status = models.ForeignKey(
        NotificationStatus,
        on_delete=models.PROTECT,
        related_name="queue_items",
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this notification should be processed."
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    retry_count = models.PositiveIntegerField(
        default=0,
    )

    max_retry = models.PositiveIntegerField(
        default=3,
    )

    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    priority = models.PositiveSmallIntegerField(
        default=5,
        help_text="Lower number = higher priority."
    )

    class Meta:

        db_table = "notification_queue"

        ordering = [
            "priority",
            "scheduled_at",
            "created_at",
        ]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["processed_at"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["recipient"]),
        ]

    def __str__(self):
        return f"{self.notification.title} -> {self.recipient.full_name}"
    
    
class NotificationLog(AuditMixin):
    """
    Stores every delivery attempt.

    Used for:
    - Email
    - WebSocket
    - Push Notification
    - SMS

    Useful for retrying failed notifications and auditing.
    """

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    recipient = models.ForeignKey(
        NotificationRecipient,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )

    retry_count = models.PositiveIntegerField(
        default=0,
    )

    response = models.JSONField(
        default=dict,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "notification_logs"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(fields=["channel"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.notification.title} ({self.channel})"