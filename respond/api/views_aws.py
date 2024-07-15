from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

import respond.api
from api.mixins import MultiSerializerCreateRetrieveMix as CreateRetrieveView
from task.base_views import TaskBuilder
from task.helpers import HttpResponseError
from geo.api.serializers import AgencyFileControlsSerializer
from inai.api import serializers
from inai.models import PetitionFileControl
from respond.models import DataFile
from task.views import build_task_params, comprobate_status


def move_and_duplicate(data_files, petition, request):
    from rest_framework.exceptions import ParseError
    from respond.models import ReplyFile
    from data_param.models import FileControl
    from classify_task.models import Stage

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
                new_file.pk = None
                new_file.petition_file_control = pet_file_ctrl
                new_file.finished_stage('initial|finished')
            else:
                data_file.petition_file_control = pet_file_ctrl
                data_file.reset_initial()

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
    serializer_class = respond.api.serializers.DataFileSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.IsAdminUser]
    action_serializers = {
        "list": respond.api.serializers.DataFileSerializer,
        "retrieve": respond.api.serializers.DataFileFullSerializer,
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
        from django.conf import settings
        from classify_task.models import Stage
        from respond.data_file_mixins.explore_mix_real import ExploreRealMix

        data_file = self.get_object()
        is_local = settings.IS_LOCAL
        if not data_file.can_repeat and not is_local:
            error = "Aún se está procesando; espera máx. 15 minutos"
            return Response({"errors": [error]}, status=status.HTTP_404_NOT_FOUND)

        stage_name = request.query_params.get("stage")
        target_stage = Stage.objects.get(name=stage_name)
        target_name = target_stage.name

        base_task = TaskBuilder(
            function_name=target_stage.main_function.name,
            models=[data_file], request=request)

        function_after = None
        if target_stage.function_after:
            function_after = target_stage.function_after.name
        # key_task, task_params = build_task_params(
        #     data_file, target_stage.main_function.name, request)

        # after_aws = "find_coincidences_from_aws" if \
        #     target_name == "cluster" else "build_sample_data_after"
        # curr_kwargs = {"after_if_empty": after_aws}
        for re_stage in target_stage.re_process_stages.all():
            current_function = re_stage.main_function.name

            # print("stage", re_stage.name, current_function)
            # task_params["models"] = [data_file]
            # method = getattr(data_file, current_function)
            re_task = TaskBuilder(
                function_name=current_function, parent_class=base_task,
                models=[data_file], request=request,
                function_after=function_after)
            explore = ExploreRealMix(
                data_file, base_task=re_task, want_response=True)
            try:
                # possible_functions: get_sample_data, verify_coincidences,
                # prepare_transform, transform_data
                getattr(explore, current_function)()
            except HttpResponseError as e:
                if e.errors:
                    data_file.save_errors(e.errors, f"{re_stage.name}|with_errors")
                return e.send_response()
            # re_task.comprobate_status(want_http_response=None
            # new_tasks, all_errors, data_file = method(task_params, **curr_kwargs)
            # if all_errors or new_tasks:
            #     if all_errors:
            #         data_file.save_errors(
            #             all_errors, f"{re_stage.name}|with_errors")
            #     return comprobate_status(
            #         key_task, all_errors, new_tasks, want_http_response=True)
            if re_stage.name == target_name:
                data_file = data_file.finished_stage(f"{target_name}|finished")
                # comprobate_status(key_task, all_errors, new_tasks)
                base_task.comprobate_status(want_http_response=False)
                data = serializers.DataFileSerializer(data_file).data
                response_body = {"data_file": data}
                return Response(response_body, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "errors": "Hubo un error inesperado en change_stage"
        })

    @action(methods=["get"], detail=True, url_path="build_columns")
    def build_columns(self, request, **kwargs):
        from respond.data_file_mixins.build_headers import BuildComplexHeaders
        data_file = self.get_object()
        from respond.data_file_mixins.explore_mix_real import ExploreRealMix

        # key_task, task_params = build_task_params(
        #     data_file, "build_columns", request)
        base_task = TaskBuilder(
            function_name="build_columns", models=[data_file], request=request)

        curr_kwargs = {
            "after_if_empty": "build_sample_data_after",
            # RICK TASK: Seguimos pendiente de qué hace esto
            "task_kwargs": {"function_after": "build_sample_data_after"},
        }
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
            return Response(data, status=status.HTTP_201_CREATED)
        except HttpResponseError as e:
            return e.send_response()

    @action(methods=["get"], detail=True, url_path="back_start")
    def back_start(self, request, **kwargs):
        from respond.api.serializers import DataFileSerializer
        data_file = self.get_object()
        data_file = data_file.reset_initial()

        data_file_full = DataFileSerializer(data_file)

        return Response(
            {"data_file_full": data_file_full.data}, status=status.HTTP_200_OK)
