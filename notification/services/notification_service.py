import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from user.models import User

from ..models import (
    Notification,
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
from .email_service import EmailService
from .preference_service import PreferenceService
from .push_service import PushService
from .queue_service import QueueService
from .template_service import TemplateService
from .websocket_service import WebSocketService

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Base exception for notification service operations."""


class RecipientService:
    """Create recipient rows for a notification in bulk."""

    @staticmethod
    def create_recipients(notification: Notification, recipients: List[User]) -> List[NotificationRecipient]:
        if not recipients:
            return []

        recipient_objs = [NotificationRecipient(notification=notification, user=user) for user in recipients]
        created = NotificationRecipient.objects.bulk_create(recipient_objs)
        return list(created)


class LogService:
    """Create queue delivery logs for notification dispatches."""

    @staticmethod
    def create_logs(
        queue_items: List[NotificationQueue],
        notification: Notification,
        recipient_map: Optional[Dict[int, NotificationRecipient]] = None,
    ) -> List[NotificationLog]:
        if not queue_items:
            return []

        log_objs: List[NotificationLog] = []
        for queue_item in queue_items:
            recipient = None
            if recipient_map:
                recipient = recipient_map.get(queue_item.recipient_id)
            if recipient is None:
                continue

            log_objs.append(
                NotificationLog(
                    notification=notification,
                    recipient=recipient,
                    channel=queue_item.channel,
                    status=queue_item.status,
                    response={},
                    retry_count=queue_item.retry_count,
                )
            )

        if not log_objs:
            return []

        return list(NotificationLog.objects.bulk_create(log_objs))


class NotificationService:
    """Orchestrates notification creation, preference checks, queueing, and delivery updates."""

    def __init__(
        self,
        template_service: type[TemplateService] = TemplateService,
        preference_service: type[PreferenceService] = PreferenceService,
        queue_service: type[QueueService] = QueueService,
        websocket_service: type[WebSocketService] = WebSocketService,
        email_service: type[EmailService] = EmailService,
        push_service: type[PushService] = PushService,
        log_service: type[LogService] = LogService,
        recipient_service: type[RecipientService] = RecipientService,
    ) -> None:
        self.template_service = template_service
        self.preference_service = preference_service
        self.queue_service = queue_service
        self.websocket_service = websocket_service
        self.email_service = email_service
        self.push_service = push_service
        self.log_service = log_service
        self.recipient_service = recipient_service

    def send_notification(
        self,
        *,
        recipients: List[User],
        category: Optional[NotificationCategory] = None,
        category_code: Optional[str] = None,
        priority: Optional[NotificationPriority] = None,
        priority_code: Optional[str] = None,
        template: Optional[NotificationTemplate] = None,
        template_code: Optional[str] = None,
        title: Optional[str] = None,
        message: Optional[str] = None,
        actor: Optional[User] = None,
        variables: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        icon: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        is_system_generated: bool = True,
    ) -> Notification:
        """Create and dispatch a notification through templates, preferences, queues, logs, and websocket."""
        validated_recipients = self._validate_recipients(recipients)
        if not validated_recipients:
            raise NotificationServiceError("At least one active recipient is required.")

        try:
            category = self._resolve_category(category=category, category_code=category_code)
            priority = self._resolve_priority(priority=priority, priority_code=priority_code)
            self._validate_configuration(category=category, priority=priority)

            template, rendered_title, rendered_message = self._resolve_template(
                template=template,
                template_code=template_code,
                title=title,
                message=message,
                variables=variables or {},
            )

            enriched_metadata = self._enrich_metadata(metadata=metadata, actor=actor)

            with transaction.atomic():
                notification = self._create_notification(
                    category=category,
                    priority=priority,
                    template=template,
                    title=rendered_title,
                    message=rendered_message,
                    action_url=action_url,
                    icon=icon,
                    metadata=enriched_metadata,
                    is_system_generated=is_system_generated,
                )
                recipient_rows = self.recipient_service.create_recipients(notification, validated_recipients)
                recipient_map = {recipient.user_id: recipient for recipient in recipient_rows}

                queue_items = self._prepare_queue_items(
                    notification=notification,
                    recipients=validated_recipients,
                    category=category,
                    priority=priority,
                    scheduled_at=scheduled_at,
                )
                self.log_service.create_logs(queue_items, notification, recipient_map)

            self._trigger_websocket(notification=notification, recipients=validated_recipients)
            logger.info("Notification created successfully for %s recipients", len(validated_recipients))
            return notification
        except NotificationServiceError:
            raise
        except ObjectDoesNotExist as exc:
            logger.exception("Notification validation failed")
            raise NotificationServiceError("Required notification configuration was not found.") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Notification creation failed")
            raise NotificationServiceError("Failed to create notification.") from exc

    def create_from_template(
        self,
        *,
        template_code: str,
        recipients: List[User],
        variables: Optional[Dict[str, Any]] = None,
        actor: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        icon: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        is_system_generated: bool = True,
    ) -> Notification:
        """Load a template, render its placeholders, and dispatch the notification."""
        template = self.template_service.get_template_by_code(template_code)
        self.template_service.validate_template(template)

        rendered_title = self.template_service.render_template(template.title, variables or {})
        rendered_message = self.template_service.render_template(template.body, variables or {})

        return self.send_notification(
            recipients=recipients,
            category=template.category,
            priority=template.priority,
            template=template,
            title=rendered_title,
            message=rendered_message,
            actor=actor,
            metadata=metadata,
            action_url=action_url,
            icon=icon,
            scheduled_at=scheduled_at,
            is_system_generated=is_system_generated,
        )

    def mark_as_read(self, recipient_id: int, user: User) -> None:
        """Mark a notification recipient as read and update unread counts via websocket."""
        try:
            with transaction.atomic():
                recipient = NotificationRecipient.objects.get(id=recipient_id, user=user, is_deleted=False)
                if not recipient.is_read:
                    recipient.is_read = True
                    recipient.read_at = timezone.now()
                    recipient.save(update_fields=["is_read", "read_at"])
        except ObjectDoesNotExist as exc:
            raise NotificationServiceError("Notification record not found.") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to mark notification as read")
            raise NotificationServiceError("Failed to mark notification as read.") from exc

        self._broadcast_unread_count(user.id)

    def mark_as_seen(self, recipient_id: int, user: User) -> None:
        """Mark a notification recipient as seen."""
        try:
            with transaction.atomic():
                recipient = NotificationRecipient.objects.get(id=recipient_id, user=user, is_deleted=False)
                if not recipient.is_seen:
                    recipient.is_seen = True
                    recipient.seen_at = timezone.now()
                    recipient.save(update_fields=["is_seen", "seen_at"])
        except ObjectDoesNotExist as exc:
            raise NotificationServiceError("Notification record not found.") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to mark notification as seen")
            raise NotificationServiceError("Failed to mark notification as seen.") from exc

    def archive_notification(self, recipient_id: int, user: User) -> None:
        """Archive a notification recipient record."""
        try:
            with transaction.atomic():
                recipient = NotificationRecipient.objects.get(id=recipient_id, user=user, is_deleted=False)
                if not recipient.is_archived:
                    recipient.is_archived = True
                    recipient.archived_at = timezone.now()
                    recipient.save(update_fields=["is_archived", "archived_at"])
        except ObjectDoesNotExist as exc:
            raise NotificationServiceError("Notification record not found.") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to archive notification")
            raise NotificationServiceError("Failed to archive notification.") from exc

    def delete_notification(self, recipient_id: int, user: User) -> None:
        """Soft-delete a notification recipient without hard deleting the record."""
        try:
            with transaction.atomic():
                recipient = NotificationRecipient.objects.get(id=recipient_id, user=user, is_deleted=False)
                recipient.soft_delete(user=user)
        except ObjectDoesNotExist as exc:
            raise NotificationServiceError("Notification record not found.") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to delete notification")
            raise NotificationServiceError("Failed to delete notification.") from exc

    def _validate_recipients(self, recipients: List[User]) -> List[User]:
        if not recipients:
            raise NotificationServiceError("At least one recipient user is required.")

        normalized: List[User] = []
        seen_ids: set[int] = set()

        for recipient in recipients:
            if recipient is None:
                continue

            recipient_id = getattr(recipient, "id", None)

            if not recipient_id:
                continue

            if recipient_id in seen_ids:
                continue

            if getattr(recipient, "is_deleted", False):
                continue

            normalized.append(recipient)
            seen_ids.add(recipient_id)

        if not normalized:
            raise NotificationServiceError("At least one valid recipient is required.")

        return normalized
    def _resolve_category(
        self,
        *,
        category: Optional[NotificationCategory],
        category_code: Optional[str],
    ) -> NotificationCategory:
        if category is not None:
            return category
        if category_code:
            try:
                return NotificationCategory.objects.get(code=category_code, is_active=True, is_deleted=False)
            except ObjectDoesNotExist as exc:
                raise NotificationServiceError("Notification category was not found or is inactive.") from exc
        raise NotificationServiceError("Notification category is required.")

    def _resolve_priority(
        self,
        *,
        priority: Optional[NotificationPriority],
        priority_code: Optional[str],
    ) -> NotificationPriority:
        if priority is not None:
            return priority
        if priority_code:
            try:
                return NotificationPriority.objects.get(code=priority_code, is_active=True, is_deleted=False)
            except ObjectDoesNotExist as exc:
                raise NotificationServiceError("Notification priority was not found or is inactive.") from exc
        raise NotificationServiceError("Notification priority is required.")

    def _resolve_template(
        self,
        *,
        template: Optional[NotificationTemplate],
        template_code: Optional[str],
        title: Optional[str],
        message: Optional[str],
        variables: Dict[str, Any],
    ) -> tuple[Optional[NotificationTemplate], str, str]:
        if template is not None:
            self.template_service.validate_template(template)
            rendered_title = self.template_service.render_template(template.title, variables)
            rendered_message = self.template_service.render_template(template.body, variables)
            return template, rendered_title, rendered_message

        if template_code:
            template_obj = self.template_service.get_template_by_code(template_code)
            self.template_service.validate_template(template_obj)
            rendered_title = self.template_service.render_template(template_obj.title, variables)
            rendered_message = self.template_service.render_template(template_obj.body, variables)
            return template_obj, rendered_title, rendered_message

        return None, title or "", message or ""

    def _validate_configuration(
        self,
        *,
        category: NotificationCategory,
        priority: NotificationPriority,
    ) -> None:
        if getattr(category, "is_deleted", False) or not getattr(category, "is_active", False):
            raise NotificationServiceError("Notification category is inactive or deleted.")
        if getattr(priority, "is_deleted", False) or not getattr(priority, "is_active", False):
            raise NotificationServiceError("Notification priority is inactive or deleted.")

    def _create_notification(
        self,
        *,
        category: NotificationCategory,
        priority: NotificationPriority,
        template: Optional[NotificationTemplate],
        title: str,
        message: str,
        action_url: Optional[str],
        icon: Optional[str],
        metadata: Optional[Dict[str, Any]],
        is_system_generated: bool,
    ) -> Notification:
        return Notification.objects.create(
            category=category,
            template=template,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            icon=icon,
            metadata=metadata or {},
            is_system_generated=is_system_generated,
        )

    def _prepare_queue_items(
        self,
        *,
        notification: Notification,
        recipients: List[User],
        category: NotificationCategory,
        priority: NotificationPriority,
        scheduled_at: Optional[datetime],
    ) -> List[NotificationQueue]:
        pending_status = NotificationStatus.objects.filter(code="pending", is_active=True).first()
        if pending_status is None:
            raise NotificationServiceError("Pending notification status was not found.")

        channels = {
            channel.code: channel
            for channel in NotificationChannel.objects.filter(is_active=True, is_deleted=False)
        }
        preferences = {
            preference.user_id: preference
            for preference in NotificationPreference.objects.filter(user__in=recipients).prefetch_related("enabled_categories")
        }

        queue_items: List[NotificationQueue] = []
        for channel_code, channel in channels.items():
            channel_recipients = [
                recipient for recipient in recipients if self._channel_is_enabled(recipient, category, preferences, channel_code)
            ]
            if not channel_recipients:
                continue

            created_items = self.queue_service.enqueue_bulk_notifications(
                notifications=[notification],
                recipients=channel_recipients,
                channel=channel,
                status=pending_status,
                scheduled_at=scheduled_at,
                priority=priority.display_order,
            )
            queue_items.extend(created_items)

        return queue_items

    def _channel_is_enabled(
        self,
        recipient: User,
        category: NotificationCategory,
        preferences: Dict[int, NotificationPreference],
        channel_code: str,
    ) -> bool:
        preference = preferences.get(getattr(recipient, "id", None))
        if preference is None:
            return channel_code in {"in_app", "email"}

        if preference.enabled_categories.exists():
            if not preference.enabled_categories.filter(id=category.id).exists():
                return False

        if channel_code == "in_app":
            return bool(preference.in_app)
        if channel_code == "email":
            return bool(preference.email)
        return False

    def _trigger_websocket(
        self,
        *,
        notification: Notification,
        recipients: List[User],
    ) -> None:
        if not recipients:
            return

        unread_counts = dict(
            NotificationRecipient.objects.filter(
                user__in=recipients,
                is_read=False,
                is_deleted=False,
            )
            .values_list("user_id")
            .annotate(count=Count("id"))
        )

        for recipient in recipients:
            recipient_id = getattr(recipient, "id", None)
            if not recipient_id:
                continue

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
            self.websocket_service.send_notification(recipient_id, payload)
            self.websocket_service.update_unread_count(recipient_id, unread_counts.get(recipient_id, 0))

    def _broadcast_unread_count(self, user_id: int) -> None:
        unread_count = NotificationRecipient.objects.filter(user_id=user_id, is_read=False, is_deleted=False).count()
        self.websocket_service.update_unread_count(user_id, unread_count)

    def _enrich_metadata(
        self,
        *,
        metadata: Optional[Dict[str, Any]],
        actor: Optional[User],
    ) -> Dict[str, Any]:
        payload = dict(metadata or {})
        if actor is not None:
            payload.setdefault("actor_id", getattr(actor, "id", None))
        return payload
