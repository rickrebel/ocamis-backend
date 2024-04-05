# -*- coding: utf-8 -*-
import respond.api.serializers
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, status)
from rest_framework.decorators import action

from inai.api.common import send_response
from inai.models import Petition, PetitionFileControl
from respond.models import DataFile

from api.mixins import (
    MultiSerializerListRetrieveMix as ListRetrieveView)

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
        from respond.models import ReplyFile
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


class OpenDataInaiViewSet(ListRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = respond.api.serializers.DataFileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["post"], detail=False, url_path='insert_xls')
    def insert_xls(self, request, **kwargs):
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
