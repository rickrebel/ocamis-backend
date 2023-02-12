import json
import channels
from channels.generic.websocket import AsyncWebsocketConsumer
# from asgiref.sync import async_to_sync
# from django.http import JsonResponse
from channels.db import database_sync_to_async
# from django.contrib.auth.models import AnonymousUser


class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self__user_id = "INVENTADO"
        await self.channel_layer.group_add(f"{self__user_id}-message", self.channel_name)
        #if self.scope["user"] is not AnonymousUser:
        #    self.user_id = self.scope["user"].id
        #    await self.channel_layer.group_add(f"{self.user_id}-message", self.channel_name)

    async def send_info_to_user_group(self, event):
        message = event["text"]
        await self.send(text_data=json.dumps(message))

    async def send_last_message(self, event):
        # last_msg = await self.get_last_message(self.user_id)
        last_msg = {"hola": "mundo", "todo": "ok"}
        last_msg["status"] = event["text"]
        await self.send(text_data=json.dumps(last_msg))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("file_process", self.channel_name)
        pass

    async def receive(self, text_data, **kwargs):
        text_data_json = json.loads(text_data)
        #message = text_data_json['message']
        message = {"hola": "mundo"}
        print("text_data_json ", text_data_json)
        # do some processing here
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def get_last_message(self, user_id):
        # message = Message.objects.filter(user_id=user_id).last()
        message = "hola get_last_message"
        # return message.message
        return message
