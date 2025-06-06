from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

import respond.api
from api.mixins import MultiSerializerCreateRetrieveMix as CreateRetrieveView
from task.builder import TaskBuilder
from task.helpers import HttpResponseError
from geo.api.serializers import AgencyFileControlsSerializer
from inai.api import serializers
from inai.models import PetitionFileControl
from respond.models import DataFile
from respond.api.serializers import DataFileSerializer, DataFileFullSerializer


def move_and_duplicate(data_files, petition, request):
    from rest_framework.exceptions import ParseError
    from respond.models import ReplyFile
    from data_param.models import FileControl

    destination = request.data.get("destination")
    is_duplicate = request.data.get("duplicate")
    # initial_stage = Stage.objects.get(name="initial")
    errors = []
    if destination == "reply_file":
        for data_file in data_files:
            ReplyFile.objects.create(
                petition=petition,
                file=data_file.file)
            if not is_duplicate:
                data_file.delete()
    elif destination:
        file_ctrl_id = int(destination)
        pet_file_ctrls = PetitionFileControl.objects.filter(
            petition=petition, file_control_id=file_ctrl_id)
        if pet_file_ctrls.exists():
            pet_file_ctrl = pet_file_ctrls.first()
        else:
            try:
                file_control = FileControl.objects.get(id=file_ctrl_id)
                pet_file_ctrl = PetitionFileControl.objects.create(
                    petition=petition,
                    file_control=file_control)
            except FileControl.DoesNotExist:
                raise ParseError(
                    detail="No se envió un id de file_control válido")
            except Exception as e:
                raise ParseError(detail=e)
        for data_file in data_files:
            if is_duplicate:
                new_file = data_file
                new_file.reset_initial(pet_file_ctrl, is_duplicate=True)
            else:
                data_file.reset_initial(pet_file_ctrl, is_duplicate=False)

    else:
        raise ParseError(detail="No se especificó correctamente el destino")

    return send_full_response(petition)


def send_full_response(petition):
    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "petition": petition_data,
        "file_controls": AgencyFileControlsSerializer(
            petition.agency).data["file_controls"],
    }
    return Response(data, status=status.HTTP_200_OK)


class DataFileViewSet(CreateRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = DataFileSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.IsAdminUser]
    action_serializers = {
        "list": DataFileSerializer,
        "retrieve": DataFileFullSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all().prefetch_related(
            "sheet_files",
            "sheet_files__laps",
            "sheet_files__laps__table_files",
        )

    @action(methods=["put"], detail=True, url_path="move")
    def move(self, request, **kwargs):
        data_file = self.get_object()
        petition = data_file.petition_file_control.petition
        return move_and_duplicate([data_file], petition, request)

    @action(methods=["get"], detail=True, url_path="change_stage")
    def change_stage(self, request, **kwargs):
        from classify_task.models import Stage
        from respond.data_file_mixins.explore_mix import ExploreRealMix

        data_file = self.get_object()
        if not data_file.can_repeat:
            error = "Aún se está procesando; espera máx. 15 minutos"
            return Response({"errors": [error]}, status=status.HTTP_404_NOT_FOUND)

        stage_name = request.query_params.get("stage")
        target_stage = Stage.objects.get(name=stage_name)
        target_name = target_stage.name

        curr_kwargs = {}
        if target_stage.function_after:
            curr_kwargs = {"function_after": target_stage.function_after}

        base_task = TaskBuilder(
            target_stage.main_function.name,
            models=[data_file], request=request)
        for re_stage in target_stage.re_process_stages.all():
            current_function = re_stage.main_function.name
            explore = ExploreRealMix(
                data_file, base_task=base_task, want_response=True)
            try:
                # possible_functions: get_sample_data, verify_coincidences,
                # prepare_transform, transform_data
                getattr(explore, current_function)(**curr_kwargs)
            except HttpResponseError as e:
                if e.errors:
                    data_file.save_errors(e.errors, f"{re_stage.name}|with_errors")
                base_task.comprobate_status(want_http_response=False)
                return e.send_response()
            on_target = re_stage.name == target_name
            if on_target:
                data_file = data_file.finished_stage(f"{target_name}|finished")
                base_task.comprobate_status(want_http_response=False)
                data = serializers.DataFileSerializer(data_file).data
                response_body = {"data_file": data}
                return Response(response_body, status=status.HTTP_200_OK)
        data = {"errors": "Hubo un error inesperado en change_stage"}
        return Response(status=status.HTTP_404_NOT_FOUND, data=data)

    @action(methods=["get"], detail=True, url_path="build_columns")
    def build_columns(self, request, **kwargs):
        from respond.data_file_mixins.build_headers import BuildComplexHeaders
        data_file = self.get_object()
        from respond.data_file_mixins.explore_mix import ExploreRealMix

        base_task = TaskBuilder(
            "build_columns", models=[data_file], request=request)

        curr_kwargs = {"function_after": "build_sample_data_after"}
        explore = ExploreRealMix(
            data_file, base_task=base_task, want_response=True)
        try:
            explore.get_sample_data(comprobate=True, **curr_kwargs)
        except HttpResponseError as e:
            return e.send_response()

        build_complex_headers = BuildComplexHeaders(
            data_file, base_task=base_task)
        try:
            data = build_complex_headers()
            base_task.comprobate_status(want_http_response=False)
            return Response(data, status=status.HTTP_201_CREATED)
        except HttpResponseError as e:
            return e.send_response()

    @action(methods=["get"], detail=True, url_path="back_start")
    def back_start(self, request, **kwargs):
        data_file = self.get_object()
        data_file = data_file.reset_initial()

        data_file_full = DataFileSerializer(data_file)

        return Response(
            {"data_file_full": data_file_full.data}, status=status.HTTP_200_OK)
