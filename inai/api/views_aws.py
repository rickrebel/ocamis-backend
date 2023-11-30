# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action

from inai.api.common import send_response
from inai.models import (
    DataFile, Petition, PetitionFileControl)

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrieveView,
    MultiSerializerListRetrieveMix as ListRetrieveView)

from rest_framework.exceptions import (PermissionDenied, ValidationError)
from geo.api.serializers import AgencyFileControlsSerializer
from task.views import comprobate_status, build_task_params

last_final_path = None


class AutoExplorePetitionViewSet(ListRetrieveView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "retrieve": serializers.PetitionFullSerializer,
    }

    def retrieve(self, request, *args, **kwargs):
        from inai.models import ReplyFile
        from data_param.models import FileControl
        from data_param.models import DataGroup

        petition = self.get_object()
        current_file_ctrl = request.query_params.get("file_ctrl", False)
        file_id = request.query_params.get("file_id", False)

        orphan_group = DataGroup.objects.get(name="orphan")
        name_control = "Archivos por agrupar. Solicitud %s" % (
            petition.folio_petition)
        prev_file_controls = FileControl.objects.filter(
            data_group=orphan_group,
            petition_file_control__petition=petition)
        created = False
        if prev_file_controls.exists():
            file_control = prev_file_controls.first()
        else:
            file_control, created = FileControl.objects.get_or_create(
                name=name_control,
                data_group=orphan_group,
                final_data=False,
                agency=petition.agency,
            )
        orphan_pfc, created_pfc = PetitionFileControl.objects \
            .get_or_create(file_control=file_control, petition=petition)
        all_tasks = []
        all_errors = []
        if file_id:
            key_task, task_params = build_task_params(
                petition, "auto_explore", request)
            all_data_files = DataFile.objects.filter(id=file_id)
            new_tasks, errors = petition.find_matches_in_children(
                all_data_files, current_file_ctrl=current_file_ctrl,
                task_params=task_params)
            all_tasks.extend(new_tasks)
            all_errors.extend(errors)
        else:
            key_task, task_params = build_task_params(
                petition, "auto_explore", request)
            reply_files = ReplyFile.objects.filter(
                petition=petition, has_data=True)
            for reply_file in reply_files:
                children_files = DataFile.objects. \
                    filter(reply_file=reply_file)
                if children_files.exists():
                    if not children_files.filter(
                        petition_file_control__file_control__data_group__name='orphan'
                    ).exists():
                        continue
                    new_tasks, new_errors = petition.find_matches_in_children(
                        children_files, current_file_ctrl=current_file_ctrl,
                        task_params=task_params)

                    all_tasks.extend(new_tasks)
                    all_errors.extend(new_errors)
                else:
                    async_task = reply_file.decompress(
                        orphan_pfc, task_params=task_params)
                    all_tasks.append(async_task)
            if not reply_files.exists():
                orphan_files = orphan_pfc.data_files.all()
                if not orphan_files.exists():
                    all_errors.append(
                        "No hay archivos huérfanos para explorar")
                else:
                    new_tasks, new_errors = petition.find_matches_in_children(
                        orphan_files, current_file_ctrl=current_file_ctrl,
                        task_params=task_params)
                    all_tasks.extend(new_tasks)
                    all_errors.extend(new_errors)
        key_task = comprobate_status(
            key_task, errors=all_errors, new_tasks=all_tasks)

        return send_response(petition, task=key_task, errors=all_errors)

    @action(detail=True, methods=["get"], url_path="finished")
    def finished(self, request, pk=None):
        petition = self.get_object()
        return send_response(petition)


def move_and_duplicate(data_files, petition, request):
    from rest_framework.exceptions import ParseError
    from inai.models import ReplyFile
    from data_param.models import FileControl
    from category.models import FileType #, StatusControl

    destination = request.data.get("destination")
    is_dupl = request.data.get("duplicate")
    #initial_status = StatusControl.objects.get(
    #    name="initial", group="process")
    errors = []
    if destination == "reply_file":
        for data_file in data_files:
            ReplyFile.objects.create(
                petition=petition,
                file=data_file.file,
                file_type_id="no_final_info")
            if not is_dupl:
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
            if is_dupl:
                data_file_id = data_file.id
                new_file = data_file
                new_file.pk = None
                new_file.petition_file_control = pet_file_ctrl
                # new_file.save()
                new_file.finished_stage('initial|finished')
            #if not is_dupl:
            else:
                data_file.petition_file_control = pet_file_ctrl
                data_file.save()
                #data_file.delete()
                #DataFile.objects.filter(id=data_file_id).delete()
    else:
        raise ParseError(detail="No se especificó correctamente el destino")

    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "petition": petition_data,
        "file_controls": AgencyFileControlsSerializer(
            petition.agency).data["file_controls"],
    }
    return Response(data, status=status.HTTP_200_OK)


class DataFileViewSet(CreateRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.IsAdminUser]
    action_serializers = {
        "list": serializers.DataFileSerializer,
        "retrieve": serializers.DataFileFullSerializer,
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

        data_file = self.get_object()
        is_local = settings.IS_LOCAL
        if not data_file.can_repeat and not is_local:
            return Response({
                "errors": ["Aún se está procesando; espera máx. 15 minutos"]
            }, status=status.HTTP_404_NOT_FOUND)
        stage_text = request.query_params.get("stage")
        target_stage = Stage.objects.get(name=stage_text)
        key_task, task_params = build_task_params(
            data_file, target_stage.main_function.name, request)
        target_name = target_stage.name
        after_aws = "find_coincidences_from_aws" if \
            target_name == "cluster" else "build_sample_data_after"
        curr_kwargs = {"after_if_empty": after_aws}
        for stage in target_stage.re_process_stages.all():
            current_function = stage.main_function.name
            print("stage", stage.name, current_function)
            task_params["models"] = [data_file]
            method = getattr(data_file, current_function)
            if not method:
                break
            new_tasks, all_errors, data_file = method(task_params, **curr_kwargs)
            if all_errors or new_tasks:
                if all_errors:
                    print("all_errors", all_errors)
                    data_file.save_errors(
                        all_errors, f"{stage.name}|with_errors")
                return comprobate_status(
                    key_task, all_errors, new_tasks, want_http_response=True)
            elif stage.name == target_name:
                data_file = data_file.finished_stage(f"{target_name}|finished")
                comprobate_status(key_task, all_errors, new_tasks)
                data = serializers.DataFileSerializer(data_file).data
                response_body = {"data_file": data}
                return Response(response_body, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "errors": "Hubo un error inesperado"
        })

    @action(methods=["get"], detail=True, url_path="build_columns")
    def build_columns(self, request, **kwargs):
        from inai.data_file_mixins.build_headers import BuildComplexHeaders
        data_file = self.get_object()
        key_task, task_params = build_task_params(
            data_file, "build_columns", request)
        curr_kwargs = {
            "after_if_empty": "build_sample_data_after",
        }
        all_tasks, all_errors, data_file = data_file.get_sample_data(
            task_params, **curr_kwargs)
        if all_tasks or all_errors:
            return comprobate_status(
                key_task, all_errors, all_tasks, want_http_response=True)
        elif data_file:
            build_complex_headers = BuildComplexHeaders(data_file)
            new_tasks, errors, data = build_complex_headers()
            # new_tasks, errors, data = data_file.build_complex_headers()
            all_errors.extend(errors or [])
            if data:
                return Response(data, status=status.HTTP_201_CREATED)
        if not all_errors:
            all_errors = ["Pasó algo extraño en build_columns, reportar a Rick"]
        return Response(
            {"errors": all_errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=True, url_path="back_start")
    def back_start(self, request, **kwargs):
        from inai.api.serializers import DataFileSerializer
        data_file = self.get_object()
        data_file.sheet_files.all().delete()
        data_file.stage_id = 'initial'
        data_file.status_id = 'finished'
        data_file.filtered_sheets = []
        data_file.total_rows = 0
        data_file.suffix = None
        data_file.error_process = None
        data_file.warnings = None
        data_file.save()

        data_file_full = DataFileSerializer(data_file)

        return Response(
            {"data_file_full": data_file_full.data}, status=status.HTTP_200_OK)


class OpenDataInaiViewSet(ListRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["post"], detail=False, url_path='insert_xls')
    def insert_xls(self, request, **kwargs):
        import json
        import zipfile
        import pandas as pd
        from datetime import datetime
        from scripts.import_inai import insert_from_json

        zip_file = zipfile.ZipFile(request.FILES['file'])
        petitions = []
        for zip_elem in zip_file.infolist():
            file_bytes = zip_file.open(zip_elem).read()
            excel_file = pd.read_excel(
                file_bytes, sheet_name="Reporte", dtype='string',
                na_filter=False, keep_default_na=False)
            # print(excel_file)
            records = excel_file.to_dict(orient='records')
            petitions += records

        for pet in petitions:
            try:
                val = pet.get("Fecha de recepción", "01/01/2018") or "01/01/2018"
                pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')
            except Exception as e:
                print(pet)
                print(e)

        petitions = sorted(petitions, key=lambda i: i['fecha_orden'])

        # all_status = {}
        # for petition in petitions:
        #     if petition["Estatus"] not in all_status:
        #         all_status[petition["Estatus"]] = [petition["Institución"]]
        #     else:
        #         all_status[petition["Estatus"]].append(petition["Institución"])
        #     #all_status[petition["Estatus"]] = True
        # print("petitions", petitions)
        #
        # return Response(
        #     {"petitions": petitions}, status=status.HTTP_201_CREATED)

        inai_fields = [
            {
                "inai_open_search": "Institución",
                "model_name": "Agency",
                "app_name": "geo",
                "final_field": "nombreSujetoObligado",
                "insert": True,
                "related": 'agency',
            },
            {
                "inai_open_search": "No. de folio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "folio_petition",
                "unique": True,
            },
            {
                "inai_open_search": False,
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "agency",
                "unique": True,
            },
            {
                "inai_open_search": "Descripción",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_petition",
                "transform": "add_br",
            },
            {
                "inai_open_search": "Fecha de recepción",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_petition",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "Estatus",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "status_petition",
                "related": "status_petition",
                "transform": "get_status_obj",
            },
            {
                "inai_open_search": "Respuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_response",
                "transform": "add_br",
            },
        ]

        spec_functions = [
            # ("insert_between_months", False),
            ("add_limit_complain", True),
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search',
            special_functions=spec_functions)

        # if data.get("errors", False):
        #    return Response(
        #        data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": True}, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path='insert_json')
    def insert_json(self, request, **kwargs):
        import json
        from datetime import datetime
        from scripts.import_inai import insert_from_json
        data_json = request.data
        data = json.load(data_json["file"])

        petitions = data["solicitudes"]

        for pet in petitions:
            val = pet["fechaEnvio"]
            pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')

        petitions = sorted(petitions, key=lambda i: i['fecha_orden'])

        inai_fields = [
            {
                "inai_open_search": "idSujetoObligado",
                "model_name": "Agency",
                "app_name": "geo",
                "final_field": "idSujetoObligado",
                "related": 'agency',
            },
            {
                "inai_open_search": "nombreSujetoObligado",
                "model_name": "Agency",
                "app_name": "geo",
                "final_field": "nombreSujetoObligado",
                # "insert": True,
                "related": 'agency',
            },
            {
                "inai_open_search": "dsFolio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "folio_petition",
                "unique": True,
            },
            {
                "inai_open_search": False,
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "agency",
                "unique": True,
            },
            {
                "inai_open_search": "descripcionSolicitud",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_petition",
                "transform": "unescape",
            },
            {
                "inai_open_search": "fechaEnvio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_petition",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "descripcionRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_response",
                "transform": "unescape",
            },
            {
                "inai_open_search": "dtFechaUltimaRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_response",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "id",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "id_inai_open_data",
            },
            {
                "inai_open_search": "informacionQueja",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "info_queja_inai",
                "transform": "to_json",
            },
        ]
        spec_functions = [
            ("join_url", True),
            ("join_lines", True),
            # ("insert_between_months", False)
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search',
            special_functions=spec_functions)

        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            data, status=status.HTTP_201_CREATED)
