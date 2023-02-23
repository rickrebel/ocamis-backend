# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action

from inai.api.common import send_response
from inai.models import (
    DataFile, Petition, PetitionFileControl)
from task.models import AsyncTask

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,
    MultiSerializerListRetrieveMix as ListRetrieveView)

from rest_framework.exceptions import (PermissionDenied, ValidationError)
from catalog.api.serializers import EntityFileControlsSerializer
from task.views import comprobate_status, build_task_params

last_final_path = None


class AutoExplorePetitionViewSet(ListRetrieveView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "retrieve": serializers.PetitionFullSerializer,
    }

    def retrieve(self, request, pk=None):
        from inai.models import FileControl, ProcessFile
        from data_param.models import DataGroup

        petition = self.get_object()
        current_file_ctrl = request.query_params.get("file_ctrl", False)
        file_id = request.query_params.get("file_id", False)

        orphan_group = DataGroup.objects.get(name="orphan")
        name_control = "Archivos por agrupar. Petición %s" % (
            petition.folio_petition)
        prev_file_controls = FileControl.objects.filter(
            data_group=orphan_group,
            petition_file_control__petition=petition)
        if prev_file_controls.exists():
            file_control = prev_file_controls.first()
        else:
            file_control, created = FileControl.objects.get_or_create(
                name=name_control,
                data_group=orphan_group,
                final_data=False,
            )
        pet_file_ctrl, created_pfc = PetitionFileControl.objects \
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
            process_files = ProcessFile.objects.filter(
                petition=petition, has_data=True)
            for process_file in process_files:
                children_files = DataFile.objects. \
                    filter(process_file=process_file)
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
                    async_task = process_file.decompress(
                        pet_file_ctrl, task_params=task_params)
                    all_tasks.append(async_task)
        key_task = comprobate_status(
            key_task, errors=all_errors, new_tasks=all_tasks)

        return send_response(petition, task=key_task, errors=all_errors)

    @action(detail=True, methods=["get"], url_path="finished")
    def finished(self, request, pk=None):
        petition = self.get_object()
        return send_response(petition)


def move_and_duplicate(data_files, petition, request):
    from rest_framework.exceptions import ParseError
    from inai.models import ProcessFile, FileControl
    from category.models import FileType #, StatusControl

    destination = request.data.get("destination")
    is_dupl = request.data.get("duplicate")
    #initial_status = StatusControl.objects.get(
    #    name="initial", group="process")
    errors = []
    if destination == "process_file":
        file_type_no_final = FileType.objects.get(name="no_final_info")
        for data_file in data_files:
            ProcessFile.objects.create(
                petition=petition,
                file=data_file.file,
                file_type=file_type_no_final)
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
                new_file.change_status('initial')
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
        "file_controls": EntityFileControlsSerializer(
            petition.entity).data["file_controls"],
    }
    return Response(data, status=status.HTTP_200_OK)


class DataFileViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
        "retrieve": serializers.DataFileEditSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["put"], detail=True, url_path="move")
    def move(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()

        data_file = self.get_object()
        petition = data_file.petition_file_control.petition
        return move_and_duplicate([data_file], petition, request)

    @action(methods=["get"], detail=True, url_path="build_sample_data")
    def build_sample_data(self, request, **kwargs):
        from inai.api.serializers import DataFileSerializer
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()
        key_task, task_params = build_task_params(
            data_file, "build_sample_data", request)
        curr_kwargs = {
            "after_if_empty": "find_coincidences_from_aws",
        }
        all_tasks, all_errors, data_file = data_file.get_sample_data(
            task_params, **curr_kwargs)

        resp = comprobate_status(
            key_task, all_errors, all_tasks, want_http_response=True)
        if resp:
            return resp

        data_file, saved, errors = data_file.find_coincidences()
        if not saved and not errors:
            errors = ["No coincide con el formato del archivo 2"]
        response_body = {}
        if errors:
            data_file.save_errors(errors, "explore_fail")
            response_body["errors"] = errors
            final_status = status.HTTP_400_BAD_REQUEST
        elif data_file:
            data = DataFileSerializer(data_file).data
            response_body["data_file"] = data
            final_status = status.HTTP_200_OK

        if response_body:
            return Response(response_body, status=final_status)
        #RICK 14
        else:
            if errors:
                print("ANALIZAR")
            else:
                if new_data_file:
                    new_data_file = new_data_file.change_status("success_exploration")
                    final_status = status.HTTP_200_OK
                else:
                    new_data_file = data_file.change_status("success_exploration")
                    final_status = status.HTTP_400_BAD_REQUEST
            if new_data_file:
                if new_data_file:
                    data = DataFileSerializer(new_data_file).data
                else:
                    data = DataFileSerializer(data_file).data
                response_body["data_file"] = data
            child_data_files = DataFile.objects.filter(
                origin_file=data_file)
            # print("child_data_files: ", child_data_files.count())
            key_task = task_params["parent_task"]
            key_task = comprobate_status(
                key_task, errors=[], new_tasks=new_tasks)
            if key_task:
                response_body["new_task"] = key_task.id
            if new_ch:
                response_body["new_files"] = DataFileSerializer(
                    new_ch, many=True).data
            return Response(response_body, status=final_status)

    @action(methods=["get"], detail=True, url_path="counting")
    def counting(self, request, **kwargs):
        from inai.api.serializers import DataFileSerializer
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()
        key_task, task_params = build_task_params(
            data_file, "counting", request)
        curr_kwargs = {
            "after_if_empty": "find_coincidences_from_aws",
        }
        all_tasks, all_errors, data_file = data_file.get_sample_data(
            task_params, **curr_kwargs)

        resp = comprobate_status(
            key_task, all_errors, all_tasks, want_http_response=True)
        if resp:
            return resp

        all_tasks, all_errors, data_file = data_file.every_has_total_rows(
            task_params)
        data_file, saved, errors = data_file.find_coincidences()



        data_file, errors, new_ch = data_file.comprobate_coincidences()
        response_body = {}
        final_status = status.HTTP_200_OK
        if data_file:
            data_rows = data_file.count_file_rows()
            data = DataFileSerializer(data_file).data
            response_body["data_file"] = data
            if data_rows.get("errors", False):
                response_body["errors"] = data_rows["errors"]
                final_status = status.HTTP_400_BAD_REQUEST
        if errors:
            response_body["errors"] = response_body.get("errors", []) + errors
            final_status = status.HTTP_400_BAD_REQUEST
        print("response_body: ", response_body)
        return Response(response_body, status=final_status)

    @action(methods=["get"], detail=True, url_path="build_columns")
    def build_columns(self, request, **kwargs):

        data_file = self.get_object()
        key_task, task_params = build_task_params(
            data_file, "build_columns", request)
        curr_kwargs = {
            "after_if_empty": "explore_data_xls_after",
        }
        all_tasks, all_errors, data_file = data_file.get_sample_data(
            task_params, **curr_kwargs)
        resp = comprobate_status(
            key_task, all_errors, all_tasks, want_http_response=True)
        if resp:
            return resp
        if data_file:
            new_tasks, errors, data = data_file.build_complex_headers()
            all_errors.extend(errors or [])
            if data:
                return Response(data, status=status.HTTP_201_CREATED)
        return Response(
            {"errors": all_errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=True, url_path="auto_explore_all")
    def auto_explore_all(self, request, **kwargs):
        return True


class OpenDataInaiViewSet(ListRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["post"], detail=False, url_path='insert_xls')
    def insert_xls(self, request, **kwargs):
        import json
        import zipfile
        import pandas as pd
        from datetime import datetime
        from scripts.import_inai import insert_from_json
        if not request.user.is_staff:
            raise PermissionDenied()

        zip_file = zipfile.ZipFile(request.FILES['file'])
        petitions = []
        for zip_elem in zip_file.infolist():
            file_bytes = zip_file.open(zip_elem).read()
            excel_file = pd.read_excel(
                file_bytes, sheet_name="Reporte", dtype='string',
                na_filter=False, keep_default_na=False)
            #print(excel_file)
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


        """
        all_status = {}
        for petition in petitions:
            if petition["Estatus"] not in all_status:
                all_status[petition["Estatus"]] = [petition["Institución"]]
            else:
                all_status[petition["Estatus"]].append(petition["Institución"])
            #all_status[petition["Estatus"]] = True
        print("petitions", petitions)
        
        return Response(
            {"petitions": petitions}, status=status.HTTP_201_CREATED)
        """

        inai_fields = [
            {
                "inai_open_search": "Institución",
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "nombreSujetoObligado",
                "insert": True,
                "related": 'entity',
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
                "final_field": "entity",
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
            ("insert_between_months", False),
            ("add_limit_complain", True),
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search',
            special_functions=spec_functions)

        #if data.get("errors", False):
        #    return Response(
        #        data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": True}, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path='insert_json')
    def insert_json(self, request, **kwargs):
        import json
        from datetime import datetime
        from scripts.import_inai import insert_from_json
        if not request.user.is_staff:
            raise PermissionDenied()
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
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "idSujetoObligado",
                "related": 'entity',
            },
            {
                "inai_open_search": "nombreSujetoObligado",
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "nombreSujetoObligado",
                # "insert": True,
                "related": 'entity',
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
                "final_field": "entity",
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
            ("insert_between_months", False)
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search',
            special_functions=spec_functions)

        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            data, status=status.HTTP_201_CREATED)

