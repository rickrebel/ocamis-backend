from inai.api import serializers
from geo.api.serializers import AgencyFileControlsSerializer
from rest_framework.response import Response
from rest_framework import status
from task.base_views import TaskBuilder


def send_response(petition, task=None, errors=None):
    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "errors": errors,
        "petition": petition_data,
        "file_controls": AgencyFileControlsSerializer(
            petition.agency).data["file_controls"],
    }

    if task:
        data["new_task"] = task.id
    return Response(data, status=status.HTTP_200_OK)


def send_response2(petition, base_task: TaskBuilder):
    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "errors": base_task.errors,
        "petition": petition_data,
        "file_controls": AgencyFileControlsSerializer(
            petition.agency).data["file_controls"],
        "new_task": base_task.main_task.id,
    }
    return Response(data, status=status.HTTP_200_OK)
