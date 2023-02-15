from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from core import routing

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(routing.websocket_urlpatterns),
    }
)
