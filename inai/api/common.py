from inai.api import serializers
from catalog.api.serializers import EntityFileControlsSerializer
from rest_framework.response import Response
from rest_framework import status

from task.api.serializers import AsyncTaskSerializer


def send_response(petition, task=None, errors=None):
    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "errors": errors,
        "petition": petition_data,
        "file_controls": EntityFileControlsSerializer(
            petition.entity).data["file_controls"],
    }

    if task:
        # current_task_data = AsyncTaskSerializer(task).data
        # data["current_task"] = current_task_data
        data["new_task"] = task.id
    return Response(data, status=status.HTTP_200_OK)
