import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shashan.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Initialize Django first
django_asgi_app = get_asgi_application()

# Import routing after Django is ready
import configuration.routing
import notification.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            configuration.routing.websocket_urlpatterns +
            notification.routing.websocket_urlpatterns
        )
    ),
})