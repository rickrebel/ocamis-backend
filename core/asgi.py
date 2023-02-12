from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from inai.consumers import MyConsumer

# path('ws/file_process/', MyConsumer.as_asgi()),

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        #path('ws/file_process/', MyConsumer.as_view()),
        path('socket.io/', MyConsumer.as_asgi()),
        # your websocket routing here
    ]),
    #'http': get_asgi_application(),
    'http': get_asgi_application(),
    #"http": channels.asgi.AsgiHandler,
})