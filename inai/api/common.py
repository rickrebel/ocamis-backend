from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from task.builder import TaskBuilder

from inai.api import serializers
from geo.api.serializers import AgencyFileControlsSerializer
from inai.models import Petition


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


def get_orphan_data_files(petition: Petition):
    detail_errors = {"errors": "No hay archivos huérfanos para explorar"}
    orphan_pfc = petition.get_orphan_pfc()
    if not orphan_pfc:
        raise ParseError(detail=detail_errors)
    data_files = orphan_pfc.data_files.all()
    if not data_files.exists():
        petition.delete_orphan_pfc()
        raise ParseError(detail=detail_errors)
    return orphan_pfc, data_files
