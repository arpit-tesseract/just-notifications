import logging
from datetime import datetime
from typing import Any, Optional

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from user.models import User

from .models import (
    Notification,
    NotificationAttachment,
    NotificationPreference,
    NotificationQueue,
    NotificationRecipient,
    NotificationTemplate,
)
from .services.notification_service import NotificationService
from .services.preference_service import PreferenceService
from .services.queue_service import QueueService
from .services.template_service import TemplateService
from .services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)


def _safe_get_notification_status_code(instance: Any) -> Optional[str]:
    status = getattr(instance, "status", None)
    return getattr(status, "code", None) if status is not None else None


@receiver(post_save, sender=User)
def create_default_notification_preference(sender: type[User], instance: User, created: bool, **kwargs: Any) -> None:
    """Create a default notification preference record for newly created users."""
    if not created:
        return

    try:
        NotificationPreference.objects.get_or_create(user=instance)
        logger.info("Created default notification preference for user %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to create default notification preference for user %s: %s", instance.id, exc)


@receiver(post_save, sender=Notification)
def enqueue_notification_on_create(sender: type[Notification], instance: Notification, created: bool, **kwargs: Any) -> None:
    """Enqueue a notification for delivery when a new notification record is created."""
    if not created or instance.is_deleted:
        return

    def _dispatch() -> None:
        try:
            queue_item = QueueService.enqueue_notification(
                notification=instance,
                recipient=instance.created_by if hasattr(instance, "created_by") else None,
                channel=instance.category if hasattr(instance, "category") else None,
                status=None,
                scheduled_at=None,
                priority=instance.priority.display_order if getattr(instance, "priority", None) else 5,
            )
            logger.info("Enqueued notification %s via queue item %s", instance.id, queue_item.id)
        except Exception as exc:
            logger.exception("Failed to enqueue notification %s: %s", instance.id, exc)

    transaction.on_commit(_dispatch)


@receiver(post_save, sender=NotificationRecipient)
def create_initial_notification_log(sender: type[NotificationRecipient], instance: NotificationRecipient, created: bool, **kwargs: Any) -> None:
    """Create a pending notification log entry for each newly created recipient record."""
    if not created:
        return

    try:
        from .models import NotificationChannel, NotificationStatus

        in_app_channel = NotificationChannel.objects.filter(code="in_app", is_active=True).first()
        pending_status = NotificationStatus.objects.filter(code="pending", is_active=True).first()
        if not in_app_channel or not pending_status:
            logger.warning("Notification log initialization skipped for recipient %s due to missing configuration", instance.id)
            return

        NotificationLog = None
        from .models import NotificationLog

        NotificationLog.objects.get_or_create(
            notification=instance.notification,
            recipient=instance,
            defaults={
                "channel": in_app_channel,
                "status": pending_status,
                "response": {},
                "retry_count": 0,
            },
        )
        logger.info("Initialized notification log for recipient %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to create notification log for recipient %s: %s", instance.id, exc)


@receiver(post_save, sender=NotificationRecipient)
def update_unread_count_on_recipient_change(sender: type[NotificationRecipient], instance: NotificationRecipient, **kwargs: Any) -> None:
    """Broadcast unread count updates when recipient state changes."""
    if not getattr(instance, "user_id", None):
        return

    try:
        unread_count = NotificationRecipient.objects.filter(user_id=instance.user_id, is_read=False, is_deleted=False).count()
        transaction.on_commit(lambda: WebSocketService.update_unread_count(instance.user_id, unread_count))
        logger.info("Broadcast unread count update for user %s", instance.user_id)
    except Exception as exc:
        logger.exception("Failed to broadcast unread count update for user %s: %s", instance.user_id, exc)


@receiver(post_delete, sender=NotificationAttachment)
def delete_notification_attachment_file(sender: type[NotificationAttachment], instance: NotificationAttachment, **kwargs: Any) -> None:
    """Delete the physical file for an attachment after the database row is removed."""
    try:
        if instance.file and instance.file.name:
            instance.file.delete(save=False)
        logger.info("Deleted attachment file for attachment %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to delete attachment file for attachment %s: %s", instance.id, exc)


@receiver(post_save, sender=Notification)
def cleanup_soft_deleted_notification(sender: type[Notification], instance: Notification, **kwargs: Any) -> None:
    """Cancel pending queue items and archive recipients for soft-deleted notifications."""
    if not instance.is_deleted:
        return

    try:
        from .models import NotificationQueue

        NotificationQueue.objects.filter(notification=instance, status__code__in=["pending", "retrying", "scheduled"]).update(status__code="cancelled")
        NotificationRecipient.objects.filter(notification=instance, is_deleted=False).update(is_archived=True, archived_at=timezone.now())
        logger.info("Soft-deleted notification %s cleanup completed", instance.id)
    except Exception as exc:
        logger.exception("Failed to cleanup soft-deleted notification %s: %s", instance.id, exc)


@receiver(post_save, sender=Notification)
def reactivate_notification_on_restore(sender: type[Notification], instance: Notification, **kwargs: Any) -> None:
    """Reactivate recipients and requeue notifications when a soft-deleted notification is restored."""
    if instance.is_deleted:
        return

    try:
        NotificationRecipient.objects.filter(notification=instance, is_deleted=True).update(is_deleted=False, archived_at=None)
        logger.info("Restored recipient state for notification %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to restore notification %s: %s", instance.id, exc)


@receiver(post_save, sender=NotificationTemplate)
def invalidate_template_cache(sender: type[NotificationTemplate], instance: NotificationTemplate, **kwargs: Any) -> None:
    """Invalidate template cache and refresh template service state after template updates."""
    try:
        TemplateService.invalidate_cache(instance.code)
        logger.info("Invalidated template cache for template %s", instance.code)
    except Exception as exc:
        logger.exception("Failed to invalidate template cache for template %s: %s", instance.code, exc)


@receiver(post_save, sender=NotificationPreference)
def clear_preference_cache(sender: type[NotificationPreference], instance: NotificationPreference, **kwargs: Any) -> None:
    """Clear cached preferences and notify the client if required."""
    try:
        PreferenceService.clear_cache(instance.user_id)
        transaction.on_commit(lambda: WebSocketService.update_unread_count(instance.user_id, 0))
        logger.info("Cleared notification preference cache for user %s", instance.user_id)
    except Exception as exc:
        logger.exception("Failed to clear preference cache for user %s: %s", instance.user_id, exc)


@receiver(post_save, sender=NotificationQueue)
def handle_queue_completion(sender: type[NotificationQueue], instance: NotificationQueue, **kwargs: Any) -> None:
    """Delegate post-delivery behavior to the notification service when a queue item completes."""
    status_code = getattr(getattr(instance, "status", None), "code", None)
    if status_code != "completed":
        return

    try:
        service = NotificationService()
        service.after_delivery(instance)
        logger.info("Executed post-delivery hook for queue item %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to execute post-delivery hook for queue item %s: %s", instance.id, exc)


@receiver(post_save, sender=NotificationQueue)
def handle_queue_failure(sender: type[NotificationQueue], instance: NotificationQueue, **kwargs: Any) -> None:
    """Retry failed queue items when allowed by retry policy."""
    status_code = getattr(getattr(instance, "status", None), "code", None)
    if status_code != "failed":
        return

    try:
        QueueService.retry_queue_item(instance)
        logger.info("Triggered retry workflow for queue item %s", instance.id)
    except Exception as exc:
        logger.exception("Failed to retry queue item %s: %s", instance.id, exc)


@receiver(pre_save, sender=Notification)
def archive_expired_notification(sender: type[Notification], instance: Notification, **kwargs: Any) -> None:
    """Archive notifications when their expiry date has been reached."""
    if instance.pk is None:
        return

    try:
        previous = Notification.objects.get(pk=instance.pk)
        if previous.is_deleted:
            return

        expires_at = instance.metadata.get("expires_at") if isinstance(instance.metadata, dict) else None
        if not expires_at:
            return

        try:
            expires_at_dt = datetime.fromisoformat(str(expires_at))
        except (TypeError, ValueError):
            return

        if expires_at_dt <= timezone.now():
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            logger.info("Marked notification %s as expired", instance.id)
    except Exception as exc:
        logger.exception("Failed to mark notification %s as expired: %s", instance.id, exc)


# This file is intended to be imported from notification/apps.py inside AppConfig.ready().
