from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(
        "sockets"
        # your websocket routing here
    ),
})