from inai.api import serializers
from geo.api.serializers import AgencyFileControlsSerializer
from rest_framework.response import Response
from rest_framework import status


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
