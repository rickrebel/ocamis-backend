from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import os
from core import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', "core.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(routing.websocket_urlpatterns),
    }
)
