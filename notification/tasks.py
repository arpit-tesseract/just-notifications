import logging
from datetime import timedelta
from smtplib import SMTPException
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.db.utils import DatabaseError, OperationalError
from django.utils import timezone

from user.models import User

from .models import (
    Notification,
    NotificationAttachment,
    NotificationCategory,
    NotificationChannel,
    NotificationLog,
    NotificationPreference,
    NotificationPriority,
    NotificationQueue,
    NotificationRecipient,
    NotificationStatus,
    NotificationTemplate,
)
from .services.email_service import EmailService, EmailServiceError
from .services.notification_service import NotificationService
from .services.preference_service import PreferenceService
from .services.push_service import PushService, PushServiceError
from .services.websocket_service import WebSocketService, WebSocketServiceError

logger = logging.getLogger(__name__)


def _get_status(code: str) -> Optional[NotificationStatus]:
    return (
        NotificationStatus.objects.filter(code=code, is_active=True).first()
        or NotificationStatus.objects.filter(code=code).first()
    )


def _get_or_create_status(code: str) -> NotificationStatus:
    status = _get_status(code)
    if status is None:
        raise NotificationStatus.DoesNotExist(f"Notification status '{code}' not found.")
    return status


def _channel_is_enabled(user: User, category: NotificationCategory, channel_code: str) -> bool:
    if not user or not getattr(user, "is_active", False):
        return False
    if category and getattr(category, "is_deleted", False):
        return False
    enabled_channels = PreferenceService.get_enabled_channels(user, category)
    return channel_code in enabled_channels


def _queue_item_context(queue_item: NotificationQueue) -> Dict[str, Any]:
    return {
        "queue_id": queue_item.id,
        "notification_id": queue_item.notification_id,
        "recipient_id": queue_item.recipient_id,
        "channel_code": queue_item.channel.code,
    }


def _update_queue_item(
    queue_item: NotificationQueue,
    status_code: str,
    *,
    error_message: Optional[str] = None,
    retry_count: Optional[int] = None,
    processed_at: Optional[timezone.datetime] = None,
    next_retry_at: Optional[timezone.datetime] = None,
) -> NotificationQueue:
    status = _get_or_create_status(status_code)
    with transaction.atomic():
        queue_item.status = status
        queue_item.error_message = error_message
        if retry_count is not None:
            queue_item.retry_count = retry_count
        if processed_at is not None:
            queue_item.processed_at = processed_at
        if next_retry_at is not None:
            queue_item.next_retry_at = next_retry_at
        elif status_code in {"delivered", "sent", "failed", "cancelled"}:
            queue_item.next_retry_at = None
        queue_item.save(update_fields=[
            "status",
            "error_message",
            "retry_count",
            "processed_at",
            "next_retry_at",
        ])
    return queue_item


def _get_or_create_log(
    queue_item: NotificationQueue,
    status_code: str,
    *,
    response: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    delivered_at: Optional[timezone.datetime] = None,
    retry_count: Optional[int] = None,
) -> NotificationLog:
    recipient = NotificationRecipient.objects.select_related("notification", "user").get(
        notification_id=queue_item.notification_id,
        user_id=queue_item.recipient_id,
        is_deleted=False,
    )
    status = _get_or_create_status(status_code)
    with transaction.atomic():
        log_entry = NotificationLog.objects.create(
            notification=queue_item.notification,
            recipient=recipient,
            channel=queue_item.channel,
            status=status,
            response=response or {},
            error_message=error_message,
            delivered_at=delivered_at,
            retry_count=retry_count if retry_count is not None else queue_item.retry_count,
        )
    return log_entry


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def process_notification_queue(self, queue_ids: Optional[Sequence[int]] = None, batch_size: int = 100) -> None:
    """Process pending notification queue items in batches and dispatch channel-specific tasks."""
    if batch_size < 1:
        batch_size = 100

    queryset = NotificationQueue.objects.select_related(
        "notification",
        "recipient",
        "channel",
        "status",
    ).filter(
        status__code__in=["pending", "retrying", "scheduled"],
        processed_at__isnull=True,
    )

    if queue_ids:
        queryset = queryset.filter(id__in=list(queue_ids))

    queryset = queryset.order_by("priority", "scheduled_at", "created_at")

    queue_items = list(queryset[:batch_size])
    if not queue_items:
        logger.info("No pending notification queue items found.")
        return

    for queue_item in queue_items:
        context = _queue_item_context(queue_item)
        if getattr(queue_item.status, "code", None) in {"sent", "delivered", "failed", "cancelled"}:
            continue
        if queue_item.scheduled_at and queue_item.scheduled_at > timezone.now():
            continue

        try:
            with transaction.atomic():
                processing_status = _get_or_create_status("processing")
                queue_item.status = processing_status
                queue_item.save(update_fields=["status"])

            channel_code = queue_item.channel.code
            if channel_code == "in_app":
                send_in_app_notification.delay(queue_item.id)
            elif channel_code == "email":
                send_email_notification.delay(queue_item.id)
            elif channel_code == "push":
                send_push_notification.delay(queue_item.id)
            else:
                logger.warning("Unsupported channel code for queue item %s: %s", queue_item.id, channel_code)
                _update_queue_item(queue_item, "failed", error_message="Unsupported channel code")
                _get_or_create_log(queue_item, "failed", error_message="Unsupported channel code")
            logger.info("Dispatched %s for queue item %s", channel_code, queue_item.id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to dispatch notification queue item %s: %s", queue_item.id, exc)
            _update_queue_item(queue_item, "failed", error_message=str(exc))
            _get_or_create_log(queue_item, "failed", error_message=str(exc))
            raise


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, WebSocketServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def process_queue_item(self, queue_item_id: int) -> None:
    """Backward-compatible wrapper for queue processing."""
    process_notification_queue(queue_ids=[queue_item_id], batch_size=1)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, WebSocketServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def send_in_app_notification(self, queue_item_id: int) -> None:
    """Send an in-app notification over Django Channels and record delivery outcome."""
    queue_item = NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").get(id=queue_item_id)
    context = _queue_item_context(queue_item)
    if queue_item.status.code in {"sent", "delivered", "cancelled"}:
        logger.info("Queue item %s already completed; skipping in-app dispatch", queue_item_id)
        return

    notification = queue_item.notification
    recipient = queue_item.recipient
    if getattr(notification, "is_deleted", False) or getattr(queue_item.recipient, "is_active", True) is False:
        _update_queue_item(queue_item, "cancelled", error_message="Notification or recipient is no longer valid")
        return

    if not _channel_is_enabled(recipient, notification.category, "in_app"):
        _update_queue_item(queue_item, "cancelled", error_message="In-app channel disabled for recipient")
        _get_or_create_log(queue_item, "cancelled", error_message="In-app channel disabled for recipient")
        return

    try:
        payload = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "action_url": notification.action_url,
            "icon": notification.icon,
            "category_code": notification.category.code,
            "priority_code": notification.priority.code,
            "created_at": notification.created_at.isoformat(),
        }
        WebSocketService.send_notification(recipient.id, payload)
        _update_queue_item(queue_item, "delivered", processed_at=timezone.now())
        _get_or_create_log(queue_item, "delivered", response={"channel": "in_app", "delivery": "websocket"}, delivered_at=timezone.now())
        logger.info("WebSocket notification delivered for queue item %s", queue_item_id)
    except Exception as exc:
        logger.exception("In-app notification failed for queue item %s: %s", queue_item_id, exc)
        _update_queue_item(queue_item, "failed", error_message=str(exc))
        _get_or_create_log(queue_item, "failed", error_message=str(exc))
        raise


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, SMTPException, EmailServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def send_email_notification(self, queue_item_id: int) -> None:
    """Send an email notification using the email service and record delivery outcome."""
    queue_item = NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").get(id=queue_item_id)
    if queue_item.status.code in {"sent", "delivered", "cancelled"}:
        logger.info("Queue item %s already completed; skipping email dispatch", queue_item_id)
        return

    notification = queue_item.notification
    recipient = queue_item.recipient
    if getattr(notification, "is_deleted", False):
        _update_queue_item(queue_item, "cancelled", error_message="Notification was deleted")
        return

    if not _channel_is_enabled(recipient, notification.category, "email"):
        _update_queue_item(queue_item, "cancelled", error_message="Email channel disabled for recipient")
        _get_or_create_log(queue_item, "cancelled", error_message="Email channel disabled for recipient")
        return

    try:
        body_text = notification.message
        body_html = f"<p>{notification.message}</p>"
        subject = notification.title
        recipient_email = getattr(recipient, "email", None) or getattr(recipient, "email_address", None)
        if not recipient_email:
            _update_queue_item(queue_item, "cancelled", error_message="Recipient email address is missing")
            _get_or_create_log(queue_item, "cancelled", error_message="Recipient email address is missing")
            return

        EmailService.send_email(
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=[],
        )
        _update_queue_item(queue_item, "delivered", processed_at=timezone.now())
        _get_or_create_log(queue_item, "delivered", response={"channel": "email"}, delivered_at=timezone.now())
        logger.info("Email notification delivered for queue item %s", queue_item_id)
    except Exception as exc:
        logger.exception("Email notification failed for queue item %s: %s", queue_item_id, exc)
        _update_queue_item(queue_item, "failed", error_message=str(exc))
        _get_or_create_log(queue_item, "failed", error_message=str(exc))
        raise


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, PushServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def send_push_notification(self, queue_item_id: int) -> None:
    """Send a push notification via the push service and record the outcome."""
    queue_item = NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").get(id=queue_item_id)
    if queue_item.status.code in {"sent", "delivered", "cancelled"}:
        logger.info("Queue item %s already completed; skipping push dispatch", queue_item_id)
        return

    notification = queue_item.notification
    recipient = queue_item.recipient
    if getattr(notification, "is_deleted", False):
        _update_queue_item(queue_item, "cancelled", error_message="Notification was deleted")
        return

    if not _channel_is_enabled(recipient, notification.category, "push"):
        _update_queue_item(queue_item, "cancelled", error_message="Push channel disabled for recipient")
        _get_or_create_log(queue_item, "cancelled", error_message="Push channel disabled for recipient")
        return

    try:
        registration_token = None
        if notification.metadata:
            registration_token = notification.metadata.get("push_token") or notification.metadata.get("device_token")
        if not registration_token:
            _update_queue_item(queue_item, "cancelled", error_message="No push registration token found")
            _get_or_create_log(queue_item, "cancelled", error_message="No push registration token found")
            return

        PushService.send_push_notification(
            registration_token=registration_token,
            title=notification.title,
            body=notification.message,
            data={
                "notification_id": str(notification.id),
                "deep_link": notification.action_url or "",
            },
            image_url=notification.metadata.get("image_url") if notification.metadata else None,
            sound=notification.metadata.get("sound", "default") if notification.metadata else "default",
            badge_count=notification.metadata.get("badge_count") if notification.metadata else None,
        )
        _update_queue_item(queue_item, "delivered", processed_at=timezone.now())
        _get_or_create_log(queue_item, "delivered", response={"channel": "push"}, delivered_at=timezone.now())
        logger.info("Push notification delivered for queue item %s", queue_item_id)
    except Exception as exc:
        logger.exception("Push notification failed for queue item %s: %s", queue_item_id, exc)
        _update_queue_item(queue_item, "failed", error_message=str(exc))
        _get_or_create_log(queue_item, "failed", error_message=str(exc))
        raise


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 3}, ignore_result=True)
def cleanup_old_notifications(self, retention_days: Optional[int] = None) -> None:
    """Soft-delete expired notification records and related queue items."""
    days = retention_days or getattr(settings, "NOTIFICATION_RETENTION_DAYS", 90)
    threshold = timezone.now() - timedelta(days=days)
    queryset = Notification.objects.filter(created_at__lt=threshold, is_deleted=False)
    count = 0
    for notification in queryset.only("id").iterator(chunk_size=500):
        if getattr(notification, "is_deleted", False):
            continue
        notification.soft_delete(user=None)
        count += 1
    logger.info("Soft-deleted %s notification records older than %s days", count, days)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 3}, ignore_result=True)
def cleanup_old_logs(self, retention_days: Optional[int] = None) -> None:
    """Delete old notification logs while preserving recent audit data."""
    days = retention_days or getattr(settings, "NOTIFICATION_LOG_RETENTION_DAYS", 90)
    threshold = timezone.now() - timedelta(days=days)
    deleted_count, _ = NotificationLog.objects.filter(created_at__lt=threshold).delete()
    logger.info("Deleted %s old notification log entries older than %s days", deleted_count, days)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def retry_failed_notifications(self, batch_size: int = 100) -> None:
    """Retry queue items that failed and are eligible for another attempt."""
    if batch_size < 1:
        batch_size = 100
    now = timezone.now()
    queue_items = list(
        NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").filter(
            status__code="failed",
            retry_count__lt=F("max_retry"),
            next_retry_at__lte=now,
        ).order_by("priority", "created_at")[:batch_size]
    )

    for queue_item in queue_items:
        if queue_item.retry_count >= queue_item.max_retry:
            continue
        delay = min(60 * (2 ** queue_item.retry_count), 3600)
        next_retry = now + timedelta(seconds=delay)
        with transaction.atomic():
            queue_item.retry_count += 1
            queue_item.status = _get_or_create_status("retrying")
            queue_item.next_retry_at = next_retry
            queue_item.error_message = None
            queue_item.save(update_fields=["retry_count", "status", "next_retry_at", "error_message"])
        process_notification_queue.apply_async(args=[ [queue_item.id] ], countdown=delay)
        logger.info("Scheduled retry for queue item %s with delay %s seconds", queue_item.id, delay)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 3}, ignore_result=True)
def schedule_notifications(self) -> None:
    """Promote scheduled queue items to pending state when their scheduled time is reached."""
    now = timezone.now()
    queue_items = NotificationQueue.objects.filter(
        scheduled_at__lte=now,
        status__code="scheduled",
    )
    updated = 0
    for queue_item in queue_items.iterator(chunk_size=500):
        with transaction.atomic():
            queue_item.status = _get_or_create_status("pending")
            queue_item.save(update_fields=["status"])
        updated += 1
    logger.info("Scheduled %s notification queue items for processing", updated)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def broadcast_notification(
    self,
    title: str,
    message: str,
    category_code: str,
    priority_code: str,
    recipient_ids: Optional[Sequence[int]] = None,
    *,
    action_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    template_code: Optional[str] = None,
    scheduled_at: Optional[timezone.datetime] = None,
    chunk_size: int = 1000,
) -> None:
    """Broadcast a notification to a large set of recipients using bulk operations and chunked processing."""
    if not recipient_ids:
        logger.warning("Broadcast notification skipped because no recipients were supplied")
        return

    if chunk_size < 1:
        chunk_size = 1000

    category = NotificationCategory.objects.filter(code=category_code, is_active=True).first()
    priority = NotificationPriority.objects.filter(code=priority_code, is_active=True).first()
    template = None
    if template_code:
        template = NotificationTemplate.objects.filter(code=template_code, is_active=True).select_related("category", "priority").first()

    if not category or not priority:
        raise ValueError("Valid category and priority codes are required")

    recipient_ids_list = list(recipient_ids)
    recipient_list = list(
        User.objects.filter(id__in=recipient_ids_list, is_active=True)
        .only("id")
        .iterator(chunk_size=chunk_size)
    )
    if not recipient_list:
        logger.info("Broadcast notification skipped because no active recipients were found")
        return

    service = NotificationService()
    for start in range(0, len(recipient_list), chunk_size):
        batch = recipient_list[start:start + chunk_size]
        try:
            service.create_bulk_notification(
                category=category,
                priority=priority,
                title=title,
                message=message,
                recipients=batch,
                template=template,
                action_url=action_url,
                metadata=metadata or {},
                is_system_generated=True,
                scheduled_at=scheduled_at,
            )
        except Exception as exc:
            logger.exception("Broadcast batch failed for recipients %s: %s", [user.id for user in batch], exc)
            raise

    logger.info("Broadcast notification dispatched to %s recipients", len(recipient_list))


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def generate_notification_statistics(self) -> None:
    """Calculate notification statistics and cache them in Redis for fast reads."""
    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = {
        "unread_count": NotificationRecipient.objects.filter(is_read=False, is_deleted=False).count(),
        "read_count": NotificationRecipient.objects.filter(is_read=True, is_deleted=False).count(),
        "today_notifications": Notification.objects.filter(created_at__gte=start_of_day).count(),
        "week_notifications": Notification.objects.filter(created_at__gte=start_of_week).count(),
        "month_notifications": Notification.objects.filter(created_at__gte=start_of_month).count(),
        "failed_notifications": NotificationQueue.objects.filter(status__code="failed").count(),
        "delivered_notifications": NotificationQueue.objects.filter(status__code__in=["delivered", "sent"]).count(),
    }
    cache.set("notification:statistics", stats, timeout=600)
    logger.info("Generated notification statistics: %s", stats)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 3}, ignore_result=True)
def mark_expired_notifications(self) -> None:
    """Mark notifications as expired when expiry metadata is present and overdue."""
    now = timezone.now()
    queryset = Notification.objects.filter(is_deleted=False, metadata__has_key="expires_at")
    updated = 0
    for notification in queryset.iterator(chunk_size=500):
        expires_at = notification.metadata.get("expires_at") if isinstance(notification.metadata, dict) else None
        if not expires_at:
            continue
        try:
            expires_at_dt = timezone.datetime.fromisoformat(expires_at)
            if expires_at_dt <= now:
                with transaction.atomic():
                    notification.is_deleted = True
                    notification.deleted_at = now
                    notification.save(update_fields=["is_deleted", "deleted_at"])
                    NotificationQueue.objects.filter(notification=notification).update(status=_get_or_create_status("cancelled"))
                updated += 1
        except (TypeError, ValueError):
            continue
    logger.info("Marked %s notifications as expired", updated)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, EmailServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def send_bulk_email_notifications(self, queue_ids: Sequence[int], *, batch_size: int = 200) -> None:
    """Deliver bulk emails in batches with logging and retry support."""
    queue_items = list(
        NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").filter(id__in=list(queue_ids))[:batch_size]
    )
    for queue_item in queue_items:
        send_email_notification.delay(queue_item.id)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError, PushServiceError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 5}, ignore_result=True)
def send_bulk_push_notifications(self, queue_ids: Sequence[int], *, batch_size: int = 200) -> None:
    """Deliver bulk push notifications in batches with chunked execution."""
    queue_items = list(
        NotificationQueue.objects.select_related("notification", "recipient", "channel", "status").filter(id__in=list(queue_ids))[:batch_size]
    )
    for queue_item in queue_items:
        send_push_notification.delay(queue_item.id)


@shared_task(bind=True, autoretry_for=(DatabaseError, OperationalError, ConnectionError, TimeoutError), retry_backoff=60, retry_jitter=True, retry_kwargs={"max_retries": 3}, ignore_result=True)
def rebuild_unread_counts(self) -> None:
    """Recalculate unread counts for all active users and push updates to clients."""
    for user in User.objects.filter(is_active=True).iterator(chunk_size=500):
        unread_count = NotificationRecipient.objects.filter(user=user, is_read=False, is_deleted=False).count()
        WebSocketService.update_unread_count(user.id, unread_count)
    logger.info("Rebuilt unread counts for all active users")
