import asyncio
import contextlib
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from user.models import User
from .models import NotificationRecipient

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Production-ready WebSocket consumer for notification delivery and actions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[Any] = None
        self.user_id: Optional[int] = None
        self.group_name: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.last_activity_at = None
        self.heartbeat_interval = getattr(settings, "NOTIFICATION_WS_HEARTBEAT_INTERVAL", 30)
        self.heartbeat_timeout = getattr(settings, "NOTIFICATION_WS_HEARTBEAT_TIMEOUT", 90)

    async def connect(self) -> None:
        """Authenticate the socket, join the user's private channel, and send initial state."""
        self.user = await self._authenticate_user()
        if not self.user or not getattr(self.user, "is_active", False):
            logger.warning("Rejected unauthenticated websocket connection")
            await self.close(code=4401)
            return

        self.user_id = self.user.id
        self.group_name = f"user_{self.user_id}"

        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except Exception as exc:
            logger.exception("Failed to accept websocket connection for user %s: %s", self.user_id, exc)
            await self.close(code=1011)
            return

        self.last_activity_at = timezone.now()
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        await self._send_connection_success()
        logger.info("WebSocket connected for user %s", self.user_id)

    async def disconnect(self, close_code: int) -> None:
        """Leave the channel group and cancel heartbeat monitoring cleanly."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.heartbeat_task

        if self.group_name and self.channel_layer:
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            except Exception as exc:
                logger.exception("Failed to leave websocket group %s: %s", self.group_name, exc)

        logger.info("WebSocket disconnected for user %s (code=%s)", self.user_id, close_code)

    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
        """Dispatch incoming client actions while keeping the handler compact."""
        if not text_data:
            return

        self.last_activity_at = timezone.now()
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON payload.")
            return

        action = data.get("action")
        if not action:
            await self._send_error("Action is required.")
            return

        action_map = {
            "mark_read": self._handle_mark_read,
            "mark_seen": self._handle_mark_seen,
            "archive": self._handle_archive,
            "restore": self._handle_restore,
            "delete": self._handle_delete,
            "refresh": self._handle_refresh,
            "ping": self._handle_ping,
            "pong": self._handle_pong,
            "get_unread_count": self._handle_get_unread_count,
            "get_recent_notifications": self._handle_get_recent_notifications,
        }

        handler = action_map.get(action)
        if handler is None:
            await self._send_error(f"Unsupported action '{action}'.")
            return

        await handler(data)

    async def notification_message(self, event: Dict[str, Any]) -> None:
        """Handle server-sent real-time notification events from the channel layer."""
        payload = event.get("payload") or {}
        notification_payload = payload.get("payload") if isinstance(payload, dict) and "payload" in payload else payload
        await self.send_json({
            "success": True,
            "event": "new_notification",
            "notification": notification_payload,
        })
        await self._send_unread_count()

    async def notification_broadcast(self, event: Dict[str, Any]) -> None:
        """Handle broadcast events sent through the channel layer."""
        payload = event.get("payload") or {}
        await self.send_json({
            "success": True,
            "event": "broadcast_message",
            "message": payload,
        })

    async def unread_count_update(self, event: Dict[str, Any]) -> None:
        """Handle unread count delta updates pushed from other parts of the system."""
        payload = event.get("payload") or {}
        await self.send_json({
            "success": True,
            "event": "unread_count_updated",
            "unread_count": payload.get("unread_count", 0),
        })

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats and disconnect idle clients."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                if not self.user_id:
                    break
                if self.last_activity_at is None:
                    self.last_activity_at = timezone.now()
                    continue

                if (timezone.now() - self.last_activity_at).total_seconds() > self.heartbeat_timeout:
                    logger.warning("Heartbeat timeout for websocket user %s", self.user_id)
                    await self.close(code=4408)
                    break

                await self.send_json({
                    "success": True,
                    "event": "ping",
                    "timestamp": timezone.now().isoformat(),
                })
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Heartbeat loop failed for user %s: %s", self.user_id, exc)

    async def _authenticate_user(self) -> Optional[Any]:
        """Authenticate the websocket connection using JWT from query parameters or headers."""
        token = self._extract_bearer_token()
        if not token:
            return None

        try:
            validated_token = AccessToken(token)
        except (InvalidToken, TokenError, Exception):
            logger.warning("Invalid JWT token provided for websocket connection")
            return None

        user_id = validated_token.payload.get("user_id")
        if not user_id:
            return None

        return await self._get_user_by_id(int(user_id))

    def _extract_bearer_token(self) -> Optional[str]:
        """Extract a JWT from the query string or Authorization header."""
        query_params = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        token = query_params.get("token", [None])[0]
        if token:
            return token

        headers = dict(self.scope.get("headers", []))
        auth_header = headers.get(b"authorization")
        if isinstance(auth_header, bytes):
            auth_header = auth_header.decode("utf-8")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1].strip()
        return None

    @database_sync_to_async
    def _get_user_by_id(self, user_id: int) -> Optional[Any]:
        """Load the user from the database without reusing stale auth state."""
        try:
            return User.objects.select_related().get(id=user_id)
        except User.DoesNotExist:
            return None

    async def _send_connection_success(self) -> None:
        """Send initial connection state to the client after successful authentication."""
        unread_count = await self._get_unread_count()
        recent_notifications = await self._get_recent_notifications(limit=10)
        payload = {
            "type": "connection_success",
            "user_id": self.user_id,
            "unread_count": unread_count,
            "connected_at": timezone.now().isoformat(),
            "latest_notifications": recent_notifications,
            "server_timestamp": timezone.now().isoformat(),
            "supported_notification_types": [
                "new_notification",
                "notification_updated",
                "notification_deleted",
                "notification_read",
                "notification_seen",
                "notification_archived",
                "notification_restored",
                "unread_count_updated",
                "queue_status",
                "system_alert",
                "maintenance_message",
                "broadcast_message",
            ],
            "supported_actions": [
                "mark_read",
                "mark_seen",
                "archive",
                "restore",
                "delete",
                "refresh",
                "ping",
                "get_unread_count",
                "get_recent_notifications",
            ],
        }
        await self.send_json(payload)

    async def _handle_mark_read(self, data: Dict[str, Any]) -> None:
        """Mark a notification recipient as read and broadcast the state change."""
        recipient = await self._validate_notification(data.get("notification_id"))
        if not recipient:
            await self._send_error("Notification not found.")
            return

        await self._set_notification_state(recipient, is_read=True, read_at=timezone.now())
        await self._broadcast_state_change("notification_read", recipient.notification_id)
        await self._send_success("notification_read", recipient.notification_id)

    async def _handle_mark_seen(self, data: Dict[str, Any]) -> None:
        """Mark a notification recipient as seen and broadcast the state change."""
        recipient = await self._validate_notification(data.get("notification_id"))
        if not recipient:
            await self._send_error("Notification not found.")
            return

        await self._set_notification_state(recipient, is_seen=True, seen_at=timezone.now())
        await self._broadcast_state_change("notification_seen", recipient.notification_id)
        await self._send_success("notification_seen", recipient.notification_id)

    async def _handle_archive(self, data: Dict[str, Any]) -> None:
        """Archive a recipient notification and broadcast the change."""
        recipient = await self._validate_notification(data.get("notification_id"))
        if not recipient:
            await self._send_error("Notification not found.")
            return

        await self._set_notification_state(recipient, is_archived=True, archived_at=timezone.now())
        await self._broadcast_state_change("notification_archived", recipient.notification_id)
        await self._send_success("notification_archived", recipient.notification_id)

    async def _handle_restore(self, data: Dict[str, Any]) -> None:
        """Restore an archived notification recipient and broadcast the change."""
        recipient = await self._validate_notification(data.get("notification_id"))
        if not recipient:
            await self._send_error("Notification not found.")
            return

        await self._set_notification_state(recipient, is_archived=False, archived_at=None)
        await self._broadcast_state_change("notification_restored", recipient.notification_id)
        await self._send_success("notification_restored", recipient.notification_id)

    async def _handle_delete(self, data: Dict[str, Any]) -> None:
        """Soft-delete a recipient notification record."""
        recipient = await self._validate_notification(data.get("notification_id"))
        if not recipient:
            await self._send_error("Notification not found.")
            return

        await self._soft_delete_recipient(recipient)
        await self._broadcast_state_change("notification_deleted", recipient.notification_id)
        await self._send_success("notification_deleted", recipient.notification_id)

    async def _handle_refresh(self, data: Dict[str, Any]) -> None:
        """Refresh unread counts and recent notifications for the client."""
        unread_count = await self._get_unread_count()
        recent_notifications = await self._get_recent_notifications(limit=10)
        await self.send_json({
            "success": True,
            "event": "refresh_complete",
            "unread_count": unread_count,
            "latest_notifications": recent_notifications,
        })

    async def _handle_ping(self, data: Dict[str, Any]) -> None:
        """Reply to ping requests with a pong response."""
        await self.send_json({
            "success": True,
            "event": "pong",
            "timestamp": timezone.now().isoformat(),
        })

    async def _handle_pong(self, data: Dict[str, Any]) -> None:
        """Update heartbeat state when the client responds to a ping."""
        self.last_activity_at = timezone.now()

    async def _handle_get_unread_count(self, data: Dict[str, Any]) -> None:
        """Return the current unread count for the authenticated user."""
        await self._send_unread_count()

    async def _handle_get_recent_notifications(self, data: Dict[str, Any]) -> None:
        """Return the latest unread notifications for the authenticated user."""
        recent_notifications = await self._get_recent_notifications(limit=10)
        await self.send_json({
            "success": True,
            "event": "recent_notifications",
            "latest_notifications": recent_notifications,
        })

    async def _send_unread_count(self) -> None:
        """Emit a lightweight unread count update to the user's group."""
        unread_count = await self._get_unread_count()
        if self.group_name and self.channel_layer:
            await self.channel_layer.group_send(self.group_name, {
                "type": "unread_count.update",
                "payload": {"unread_count": unread_count},
            })

    async def _broadcast_state_change(self, event_name: str, notification_id: int) -> None:
        """Broadcast a state change event to the user's private notification group."""
        if self.group_name and self.channel_layer:
            await self.channel_layer.group_send(self.group_name, {
                "type": "notification.message",
                "payload": {
                    "event": event_name,
                    "notification_id": notification_id,
                    "user_id": self.user_id,
                },
            })
        await self._send_unread_count()

    async def _send_success(self, event_name: str, notification_id: Optional[int] = None) -> None:
        """Send a success payload in a consistent envelope."""
        payload = {
            "success": True,
            "event": event_name,
        }
        if notification_id is not None:
            payload["notification_id"] = notification_id
        await self.send_json(payload)

    async def _send_error(self, message: str) -> None:
        """Send a uniform error payload."""
        await self.send_json({
            "success": False,
            "message": message,
        })

    @database_sync_to_async
    def _validate_notification(self, notification_id: Optional[Any]) -> Optional[NotificationRecipient]:
        """Validate that the notification belongs to the authenticated user and is still active."""
        if not notification_id:
            return None
        try:
            notification_id_int = int(notification_id)
        except (TypeError, ValueError):
            return None

        try:
            return NotificationRecipient.objects.select_related(
                "notification",
                "notification__category",
                "notification__priority",
            ).get(user_id=self.user_id, notification_id=notification_id_int, is_deleted=False)
        except NotificationRecipient.DoesNotExist:
            return None

    @database_sync_to_async
    def _set_notification_state(
        self,
        recipient: NotificationRecipient,
        *,
        is_read: Optional[bool] = None,
        is_seen: Optional[bool] = None,
        is_archived: Optional[bool] = None,
        read_at: Optional[object] = None,
        seen_at: Optional[object] = None,
        archived_at: Optional[object] = None,
    ) -> None:
        """Update the recipient record safely and persist it in one transaction."""
        if is_read is not None:
            recipient.is_read = is_read
            recipient.read_at = read_at
        if is_seen is not None:
            recipient.is_seen = is_seen
            recipient.seen_at = seen_at
        if is_archived is not None:
            recipient.is_archived = is_archived
            recipient.archived_at = archived_at
        recipient.save(update_fields=[
            "is_read",
            "read_at",
            "is_seen",
            "seen_at",
            "is_archived",
            "archived_at",
        ])

    @database_sync_to_async
    def _soft_delete_recipient(self, recipient: NotificationRecipient) -> None:
        """Soft-delete the recipient row without affecting other devices."""
        recipient.soft_delete(user=self.user)

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        """Return the current unread count for the authenticated user."""
        return NotificationRecipient.objects.filter(user_id=self.user_id, is_read=False, is_deleted=False).count()

    @database_sync_to_async
    def _get_recent_notifications(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Return a compact list of recent unread notifications for the authenticated user."""
        recipients = NotificationRecipient.objects.filter(
            user_id=self.user_id,
            is_read=False,
            is_deleted=False,
        ).select_related(
            "notification",
            "notification__category",
            "notification__priority",
        ).order_by("-created_at")[:limit]

        return [
            {
                "id": recipient.notification_id,
                "title": recipient.notification.title,
                "message": recipient.notification.message,
                "category": recipient.notification.category.code if recipient.notification.category else None,
                "priority": recipient.notification.priority.code if recipient.notification.priority else None,
                "action_url": recipient.notification.action_url,
                "icon": recipient.notification.icon,
                "created_at": recipient.notification.created_at.isoformat(),
                "is_read": recipient.is_read,
                "is_seen": recipient.is_seen,
                "is_archived": recipient.is_archived,
            }
            for recipient in recipients
        ]


class AdminNotificationConsumer(NotificationConsumer):
    """Administrative websocket consumer for notification management workflows."""


class BroadcastConsumer(NotificationConsumer):
    """Broadcast websocket consumer for system-wide announcements."""


class QueueMonitorConsumer(NotificationConsumer):
    """Queue monitoring websocket consumer for delivery status updates."""

