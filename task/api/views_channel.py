from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MessageSendAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        # print("MessageSendAPIView GET")
        channel_layer = get_channel_layer()
        # print("channel_layer:", channel_layer)
        # get the channel group name
        async_to_sync(channel_layer.group_send)(
            "dashboard", {"type": "send_info_to_user_group",
                          "text": {"status": "done"}}
        )

        return Response({"status": True}, status=status.HTTP_200_OK)

    def post(self, request):
        # msg = Message.objects.create(user=request.user, message={
        #                             "message": request.data["message"]})
        # socket_message = f"Message with id {msg.id} was created!"
        socket_message = "Message was created!"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"{request.user.id}-message", {"type": "send_last_message",
                                           "text": socket_message}
        )

        return Response({"status": True}, status=status.HTTP_201_CREATED)
