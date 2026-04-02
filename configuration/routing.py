from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Example URL: ws://127.0.0.1:8000/ws/notifications/5/ (where 5 is the user_id)
    re_path(r'^ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
]