import logging
from typing import Any, Dict
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class WebSocketServiceError(Exception):
    """Base exception for all WebSocket service errors."""
    pass


class WebSocketService:
    """
    Service responsible for dispatching real-time notifications to users
    via Django Channels and ASGI layer.
    """

    @classmethod
    def send_notification(cls, user_id: int, payload: Dict[str, Any]) -> None:
        """
        Sends an in-app notification payload to a specific user's channel group.

        Args:
            user_id (int): The ID of the recipient user.
            payload (Dict[str, Any]): The JSON payload containing message details.

        Raises:
            WebSocketServiceError: If communication with ASGI channel layer fails.
        """
        if not user_id:
            raise WebSocketServiceError("user_id is required to send individual notifications.")

        group_name = f"user_{user_id}"
        cls._send_to_group(group_name, {
            "type": "notification.message",
            "payload": payload
        })

    @classmethod
    def broadcast(cls, payload: Dict[str, Any]) -> None:
        """
        Broadcasts an in-app notification to all active web socket clients.

        Args:
            payload (Dict[str, Any]): The JSON payload to broadcast.

        Raises:
            WebSocketServiceError: If communication with ASGI channel layer fails.
        """
        group_name = "notifications_broadcast"
        cls._send_to_group(group_name, {
            "type": "notification.broadcast",
            "payload": payload
        })

    @classmethod
    def update_unread_count(cls, user_id: int, count: int) -> None:
        """
        Pushes a real-time badge count update to a specific user's client.

        Args:
            user_id (int): The ID of the recipient user.
            count (int): The count of unread notifications.

        Raises:
            WebSocketServiceError: If communication with ASGI channel layer fails.
        """
        if not user_id:
            raise WebSocketServiceError("user_id is required to update unread count.")

        group_name = f"user_{user_id}"
        cls._send_to_group(group_name, {
            "type": "unread_count.update",
            "payload": {
                "unread_count": count
            }
        })

    @classmethod
    def _send_to_group(cls, group_name: str, message: Dict[str, Any]) -> None:
        """
        Internal helper to send sync ASGI payloads to a group.
        """
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("ASGI channel layer is not configured or available. WebSocket message discarded.")
            return

        try:
            async_to_sync(channel_layer.group_send)(group_name, message)
        except Exception as e:
            logger.error(f"Failed sending WebSocket message to group '{group_name}': {str(e)}")
            raise WebSocketServiceError(f"WebSocket group dispatch failed: {str(e)}") from e
