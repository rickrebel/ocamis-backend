from django.urls import re_path, path

from inai.consumers import MyConsumer

websocket_urlpatterns = [
    path('socket.io/', MyConsumer.as_asgi()),
    #re_path(r'ws/chat/(?P<room_name>\w+)/$', MyConsumer.as_asgi()),
]
