from django.urls import path

from inai import consumers

websocket_urlpatterns = [
    path('msg', consumers.MyConsumer.as_asgi()),
    path('socket.io', consumers.MyConsumer.as_asgi()),
]
