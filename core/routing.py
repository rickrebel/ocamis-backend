from django.urls import path, re_path

from inai import consumers

websocket_urlpatterns = [
    # path('msg/', consumers.MyConsumer.as_asgi()),
    # path('msg/', consumers.MyFinalConsumer.as_asgi()),
    re_path('msg/', consumers.MyFinalConsumer.as_asgi()),
]
