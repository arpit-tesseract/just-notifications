from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import AuditMixin, SoftDeleteMixin


class NotificationType(models.TextChoices):
    SYSTEM = "SYSTEM", _("System")
    USER = "USER", _("User")
    PRODUCT = "PRODUCT", _("Product")
    ORDER = "ORDER", _("Order")
    PAYMENT = "PAYMENT", _("Payment")
    INVENTORY = "INVENTORY", _("Inventory")
    PROFILE = "PROFILE", _("Profile")
    SECURITY = "SECURITY", _("Security")
    GENERAL = "GENERAL", _("General")


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

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
    )

    body = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )

    priority = models.CharField(
        max_length=20,
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
            models.Index(fields=["notification_type"]),
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

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )

    priority = models.CharField(
        max_length=20,
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
            models.Index(fields=["notification_type"]),
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

    push = models.BooleanField(
        default=True,
        help_text="Receive push notifications.",
    )

    '''sms = models.BooleanField(
        default=False,
        help_text="Receive SMS notifications.",
    )'''

    order_notifications = models.BooleanField(
        default=True,
    )

    payment_notifications = models.BooleanField(
        default=True,
    )

    inventory_notifications = models.BooleanField(
        default=True,
    )

    product_notifications = models.BooleanField(
        default=True,
    )

    profile_notifications = models.BooleanField(
        default=True,
    )

    security_notifications = models.BooleanField(
        default=True,
    )

    marketing_notifications = models.BooleanField(
        default=False,
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

    class DeliveryChannel(models.TextChoices):
        IN_APP = "IN_APP", "In App"
        EMAIL = "EMAIL", "Email"
        PUSH = "PUSH", "Push Notification"
        SMS = "SMS", "SMS"

    class DeliveryStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"

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
        choices=DeliveryChannel.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
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