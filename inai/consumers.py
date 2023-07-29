import json
import channels
from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer)


class MyFinalConsumer(AsyncJsonWebsocketConsumer):
    groups = ["dashboard"]

    async def connect(self):
        print("Connect------")
        await self.accept()
        await self.channel_layer.group_add("dashboard", self.channel_name)

    async def receive(self, text_data, **kwargs):
        print("receive: ", text_data)
        try:
            text_data_json = json.loads(text_data)
        except json.decoder.JSONDecodeError:
            text_data_json = text_data
        print("text_data_json", text_data_json)
        # await self.send_json({'message': text_data_json})

    async def send_info_to_user_group(self, event):
        print("send_info_to_user_group: ", event)
        message = event["text"]
        await self.send_json({'message': message})

    async def send_last_message(self, event):
        last_msg = {
            "hola": "mundo send_last_message",
            "todo": "ok",
            "status": event["text"]
        }
        await self.send(text_data=json.dumps(last_msg))

    async def send_task_info(self, event):
        # last_msg["status"] = event["text"]
        result = event["result"]
        print(
            "ENVIANDOOO: ",
            result["task_data"]["status_task"],
            result["task_data"]["task_function"])
        await self.send_json(result)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard", self.channel_name)
        pass


class MyConsumer(AsyncWebsocketConsumer):
    groups = ["dashboard"]

    async def connect(self):
        await self.accept()
        print("CONECTADO EN CONSUMERS")
        # self__user_id = "INVENTADO"
        # await self.channel_layer.group_add(f"{self__user_id}-message", self.channel_name)
        await self.channel_layer.group_add("dashboard", self.channel_name)
        # if self.scope["user"] is not AnonymousUser:
        #    self.user_id = self.scope["user"].id
        #    await self.channel_layer.group_add(f"{self.user_id}-message", self.channel_name)

    async def send_info_to_user_group(self, event):
        print("send_info_to_user_group: ", event)
        message = event["text"]
        await self.send(text_data=json.dumps(message))

    async def send_last_message(self, event):
        last_msg = {"hola": "mundo send_last_message", "todo": "ok"}
        last_msg["status"] = event["text"]
        await self.send(text_data=json.dumps(last_msg))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("file_process", self.channel_name)
        pass

    async def receive(self, text_data, **kwargs):
        print("receive: ", text_data)
        try:
            text_data_json = json.loads(text_data)
        except json.decoder.JSONDecodeError:
            text_data_json = text_data
        # text_data_json = json.loads(text_data)
        #message = text_data_json['message']
        print("text_data_json", text_data_json)
        # do some processing here
        await self.send(text_data=json.dumps({
            'message': message
        }))
