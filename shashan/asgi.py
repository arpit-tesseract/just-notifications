import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shashan.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import configuration.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,   # ✅ explicit assignment
    "websocket": AuthMiddlewareStack(
        URLRouter(
            configuration.routing.websocket_urlpatterns
        )
    ),
})