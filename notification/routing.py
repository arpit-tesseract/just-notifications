from django.urls import re_path

from .consumers import (
    AdminNotificationConsumer,
    BroadcastConsumer,
    NotificationConsumer,
    QueueMonitorConsumer,
)

app_name = "notification"

WEBSOCKET_VERSION_PREFIX = r"ws/v1"

# User Routes
websocket_urlpatterns = [
    re_path(
        rf"^/{WEBSOCKET_VERSION_PREFIX}/notifications/$",
        NotificationConsumer.as_asgi(),
        name="notification-consumer",
    ),
    re_path(
        rf"^/{WEBSOCKET_VERSION_PREFIX}/admin/notifications/$",
        AdminNotificationConsumer.as_asgi(),
        name="admin-notification-consumer",
    ),
    re_path(
        rf"^/{WEBSOCKET_VERSION_PREFIX}/broadcast/$",
        BroadcastConsumer.as_asgi(),
        name="broadcast-consumer",
    ),
    re_path(
        rf"^/{WEBSOCKET_VERSION_PREFIX}/notification-queue/$",
        QueueMonitorConsumer.as_asgi(),
        name="queue-monitor-consumer",
    ),
]
