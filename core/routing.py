import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

from inai import routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ws.settings")


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)),
    }
)
