import logging
from datetime import timedelta
from typing import List, Optional
from django.utils import timezone
from django.db import transaction
from celery import current_app

from user.models import User
from ..models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationQueue,
)

logger = logging.getLogger(__name__)


class QueueServiceError(Exception):
    """Base exception for all Queue service errors."""
    pass


class QueueService:
    """
    Service responsible for queuing notification tasks.
    Creates NotificationQueue DB records and pushes them to Celery brokers.
    """

    @classmethod
    def enqueue_notification(
        cls,
        notification: Notification,
        recipient: User,
        channel: NotificationChannel,
        status: NotificationStatus,
        scheduled_at: Optional[timezone.datetime] = None,
        priority: int = 5,
        max_retry: int = 3
    ) -> NotificationQueue:
        """
        Pushes a single notification to the Queue.

        Args:
            notification (Notification): The target notification record.
            recipient (User): The target recipient user.
            channel (NotificationChannel): The communication channel to use.
            status (NotificationStatus): Initial status (usually 'Pending').
            scheduled_at (Optional[datetime]): Timestamp for scheduled dispatch.
            priority (int): Dispatch priority (lower number = higher priority).
            max_retry (int): Max retry count.

        Returns:
            NotificationQueue: The created queue item.

        Raises:
            QueueServiceError: If DB execution or celery dispatch fails.
        """
        try:
            queue_item = NotificationQueue.objects.create(
                notification=notification,
                recipient=recipient,
                channel=channel,
                status=status,
                scheduled_at=scheduled_at,
                priority=priority,
                max_retry=max_retry
            )

            # Trigger celery task if not scheduled in future
            if not scheduled_at or scheduled_at <= timezone.now():
                cls.trigger_celery_task(queue_item.id)

            return queue_item
        except Exception as e:
            logger.error(f"Failed to enqueue notification for recipient {recipient.id}: {str(e)}")
            raise QueueServiceError(f"Enqueue operation failed: {str(e)}") from e

    @classmethod
    def enqueue_bulk_notifications(
        cls,
        notifications: List[Notification],
        recipients: List[User],
        channel: NotificationChannel,
        status: NotificationStatus,
        scheduled_at: Optional[timezone.datetime] = None,
        priority: int = 5,
        max_retry: int = 3
    ) -> List[NotificationQueue]:
        """
        Optimized bulk insert method for high-volume notification triggers (millions of users).
        Uses bulk_create for database optimization and sends bulk tasks to Celery.

        Args:
            notifications (List[Notification]): The notification objects (must map 1-1 with recipients, or list of size 1).
            recipients (List[User]): List of recipient users.
            channel (NotificationChannel): The communication channel.
            status (NotificationStatus): The status model object.
            scheduled_at (Optional[datetime]): Scheduled send timestamp.
            priority (int): Dispatch priority.
            max_retry (int): Max retry attempts.

        Returns:
            List[NotificationQueue]: List of created NotificationQueue items.
        """
        if not recipients:
            return []

        # Determine if we have one notification for all, or 1-1 mapping
        is_single_notification = len(notifications) == 1

        if not is_single_notification and len(notifications) != len(recipients):
            raise QueueServiceError("Length of notifications list must either be 1 or equal to the recipients list.")

        queue_items = []
        for index, recipient in enumerate(recipients):
            notification = notifications[0] if is_single_notification else notifications[index]
            queue_items.append(
                NotificationQueue(
                    notification=notification,
                    recipient=recipient,
                    channel=channel,
                    status=status,
                    scheduled_at=scheduled_at,
                    priority=priority,
                    max_retry=max_retry
                )
            )

        try:
            with transaction.atomic():
                # Perform high-performance batch creation
                created_items = NotificationQueue.objects.bulk_create(queue_items)

            # Trigger Celery processing for items that are due immediately
            if not scheduled_at or scheduled_at <= timezone.now():
                for item in created_items:
                    cls.trigger_celery_task(item.id)

            return created_items
        except Exception as e:
            logger.error(f"Bulk enqueue failed: {str(e)}")
            raise QueueServiceError(f"Bulk enqueue database operation failed: {str(e)}") from e

    @classmethod
    def retry_queue_item(cls, queue_item: NotificationQueue) -> NotificationQueue:
        """Move a failed queue item into a retrying state and schedule a follow-up attempt."""
        try:
            with transaction.atomic():
                retry_status = NotificationStatus.objects.filter(code="retrying", is_active=True).first()
                if retry_status is None:
                    retry_status = queue_item.status
                queue_item.retry_count = min(queue_item.retry_count + 1, queue_item.max_retry)
                queue_item.status = retry_status
                queue_item.error_message = None
                queue_item.next_retry_at = timezone.now() + timedelta(minutes=1)
                queue_item.save(update_fields=["retry_count", "status", "error_message", "next_retry_at"])
            return queue_item
        except Exception as exc:
            logger.error(f"Failed to retry queue item {queue_item.id}: {str(exc)}")
            raise QueueServiceError(f"Retry operation failed: {str(exc)}") from exc

    @classmethod
    def trigger_celery_task(cls, queue_item_id: int, delay_seconds: int = 0) -> None:
        """
        Fires a Celery task asynchronously using the app registry.
        Uses string task identifier to prevent circular import issues.

        Args:
            queue_item_id (int): ID of the NotificationQueue record to process.
            delay_seconds (int): Delay in seconds before running (for retries/scheduled items).
        """
        task_name = "notification.tasks.process_queue_item"
        try:
            if delay_seconds > 0:
                current_app.send_task(
                    task_name,
                    args=[queue_item_id],
                    countdown=delay_seconds
                )
            else:
                current_app.send_task(
                    task_name,
                    args=[queue_item_id]
                )
            logger.debug(f"Dispatched Celery task '{task_name}' for Queue Item ID {queue_item_id}.")
        except Exception as e:
            logger.critical(
                f"Celery cluster offline! Critical failure to schedule task for Queue Item ID {queue_item_id}: {str(e)}"
            )
            # Do not raise here to prevent rolling back successful database transactions.
            # A fallback management command or cron scheduler can pick up orphaned DB queue items.
