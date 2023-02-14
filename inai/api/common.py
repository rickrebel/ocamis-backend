from inai.api import serializers
from catalog.api.serializers import EntityFileControlsSerializer
from rest_framework.response import Response
from rest_framework import status


def send_response(petition, task=None, errors=None):
    petition_data = serializers.PetitionFullSerializer(petition).data
    # tasks_data = serializers.AsyncTaskSerializer(all_tasks, many=True).data
    data = {
        "errors": errors,
        "petition": petition_data,
        "file_controls": EntityFileControlsSerializer(
            petition.entity).data["file_controls"],
    }
    if task:
        current_task_data = serializers.AsyncTaskSerializer(task).data
        data["current_task"] = current_task_data
    return Response(data, status=status.HTTP_200_OK)
