# -*- coding: utf-8 -*-
import respond.api.serializers
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, status)
from rest_framework.decorators import action

from task.builder import TaskBuilder
from task.helpers import HttpResponseError
from inai.api.common import send_response, send_response2, get_orphan_data_files

from inai.models import Petition
from inai.petition_mixins.petition_mix import PetitionTransformMix
from respond.reply_file_mixins.reply_mix import ReplyFileMixReal
from respond.models import DataFile
from api.mixins import MultiSerializerListRetrieveMix as ListRetrieveView

last_final_path = None


def send_find_matches(data_files, petition, base_task):
    petition_class = PetitionTransformMix(
        petition, data_files, base_task=base_task)
    try:
        petition_class.find_matches_for_data_files()
    except HttpResponseError as e:
        print("Error en send_find_matches 1: ", e)
        return send_response2(petition, base_task)
    except Exception as e:
        print("Error en send_find_matches 2: ", e)
        return send_response2(petition, base_task)
    return send_response2(petition, base_task)


class AutoExplorePetitionViewSet(ListRetrieveView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "retrieve": serializers.PetitionFullSerializer,
    }

    def retrieve(self, request, *args, **kwargs):

        petition = self.get_object()
        orphan_pfc, data_files = get_orphan_data_files(petition)

        base_task = TaskBuilder(
            "auto_explore", models=[petition, orphan_pfc], request=request)
        return send_find_matches(data_files, petition, base_task)
        # petition_class = PetitionTransformMix(
        #     petition, data_files, base_task=base_task)
        # try:
        #     petition_class.find_matches_for_data_files()
        # except HttpResponseError as e:
        #     return send_response2(petition, base_task)
        # except Exception as e:
        #     return send_response2(petition, base_task)

    @action(detail=True, methods=["get"], url_path="data_file")
    def data_file(self, request, *args, **kwargs):

        petition = self.get_object()
        file_id = request.query_params.get("file_id", False)
        try:
            data_file = DataFile.objects.get(id=file_id)
        except DataFile.DoesNotExist:
            error = "No se encontró el archivo para explorar"
            return send_response(petition, errors=[error])

        base_task = TaskBuilder(
            "auto_explore_file", models=[petition, data_file], request=request)
        return send_find_matches([data_file], petition, base_task)
        # petition_class = PetitionTransformMix(
        #     petition, [data_file], base_task=base_task)
        # petition_class.find_matches_for_data_files()
        #
        # return send_response2(petition, base_task)

    @action(detail=True, methods=["get"], url_path="pull_orphans")
    def pull_orphans(self, request, *args, **kwargs):
        from data_param.models import FileControl

        petition: Petition = self.get_object()
        orphan_pfc, data_files = get_orphan_data_files(petition)

        file_ctrl_id = request.query_params.get("file_ctrl", False)
        if not file_ctrl_id:
            error = "No se encontró el control de archivo"
            return send_response(petition, errors=[error])
        file_control = FileControl.objects.filter(id=file_ctrl_id).first()

        base_task = TaskBuilder(
            "pull_orphans", models=[petition, file_control], request=request)
        petition_class = PetitionTransformMix(
            petition, data_files, base_task=base_task)
        petition_class.match_direct_for_data_files(file_control)
        base_task.comprobate_status()

        return send_response2(petition, base_task)

    @action(detail=True, methods=["get"], url_path="decompress_remain")
    def decompress_remain(self, request, pk=None):
        from rest_framework.exceptions import ParseError
        from respond.models import ReplyFile

        petition = self.get_object()

        remain_reply_files = ReplyFile.objects.filter(
            petition=petition, has_data=True, data_file_childs__isnull=True)
        if not remain_reply_files.exists():
            raise ParseError(
                detail={"errors": ["No hay archivos por descomprimir"]})

        base_task = TaskBuilder(
            "decompress_remain", models=[petition], request=request)

        for reply_file in remain_reply_files:
            reply_file_class = ReplyFileMixReal(reply_file, base_task=base_task)
            reply_file_class.decompress_reply()

        base_task.comprobate_status()

        return send_response2(petition, base_task)

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
            petitions, columns=inai_fields, main_app='inai',
            main_model='Petition', main_key='inai_open_search',
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
                "inai_open_search": "archivoAdjuntoRespuesta",
                "transform": "join_url",
            },
            {
                "inai_open_search": "informacionQueja",
                "transform": "to_json",
            },
        ]
        spec_functions = [
            # ("join_url", True),
            ("join_lines", True),
            # ("to_json", True),
            # ("insert_between_months", False)
        ]
        insert_from_json(
            petitions, columns=inai_fields, main_app='inai',
            main_model='Petition', main_key='inai_open_search',
            special_functions=spec_functions)

        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path='insert_json_email')
    def insert_json_email(self, request, **kwargs):
        import json
        import re
        import zipfile
        from datetime import datetime
        from scripts.import_inai import insert_from_json

        all_folios = Petition.objects.values_list('folio_petition', flat=True)
        all_folios = set(all_folios)

        pattern_lines = r'{"Folio":(.*?)}'
        pattern_lines = re.compile(pattern_lines)
        # second_pattern = r'^(.*?)"DescripcionSolicitud":"(.*?)","FechaRespuesta":"(.*)"$'
        second_pattern = (r'^(.*)"DescripcionSolicitud":"(.*)'
                          r'","OtrosDatos":"(.*)'
                          r'","TextoRespuesta":"(.*?)'
                          r'","FechaRespuesta":"(.*)"$')
        second_pattern = re.compile(second_pattern)
        final_petitions = []

        def clean_content(content):
            try:
                all_lines = pattern_lines.findall(content)
            except Exception as e:
                print(f"Error en content: {e}")
                # print(content)
                raise e
            for line in all_lines:
                try:
                    line_matches = second_pattern.findall(line)[0]
                    between = line_matches[1]
                    between = between.replace("\"", "*")
                    between2 = line_matches[3]
                    between2 = between2.replace("\"", "*")
                    final_line = (f'"Folio":{line_matches[0]}'
                                  f'"DescripcionSolicitud":"{between}",'
                                  f'"OtrosDatos":"{line_matches[2]}",'
                                  f'"TextoRespuesta":"{between2}",'
                                  f'"FechaRespuesta":"{line_matches[4]}"')
                    # final_petitions.append("{" + final_line + "}")
                except Exception as e:
                    print(f"Error extraño: {e}")
                    print(line)
                    example = line
                    break
                try:
                    json_line = json.loads('{' + final_line + '}')
                    folio = json_line["Folio"]
                    # print(f"folio: {folio}")
                    if folio in all_folios:
                        final_petitions.append(json_line)
                except Exception as e:
                    print(f"Error en json: {e}")
                    print(final_line)
                    break

        # print("FILES", request.FILES)
        zip_file = zipfile.ZipFile(request.FILES['file'])
        data = None
        for zip_elem in zip_file.infolist():
            file_bytes = zip_file.open(zip_elem).read()
            file_content = file_bytes.decode("latin-1")
            clean_content(file_content)
        print("final_petitions", len(final_petitions))
        # return Response(
        #     {"success": True}, status=status.HTTP_201_CREATED)

        for pet in final_petitions:
            val = pet["FechaSolicitud"]
            pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')

        petitions = sorted(final_petitions, key=lambda i: i['fecha_orden'])

        inai_json_fields = [
            {
                "inai_open_search": "Dependencia",
                "model_name": "Agency",
                "app_name": "geo",
                "final_field": "nombreSujetoObligado",
                # "insert": True,
                "related": 'agency',
            },
            {
                "inai_open_search": "Folio",
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
                "inai_open_search": "Estatus",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "status_petition",
                "related": "status_petition",
                "transform": "get_status_obj",
            },
            {
                "inai_open_search": "DescripcionSolicitud",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_petition",
                "transform": "unescape",
            },
            {
                "inai_open_search": "FechaSolicitud",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_petition",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "FechaLimite",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "response_limit",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "FechaRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_response",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "TextoRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_response",
                "transform": "unescape",
            },
            {
                "inai_open_search": "id",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "id_inai_open_data",
            },
            {
                "inai_open_search": "ArchivosAdjuntos",
                "transform": "join_url",
            },
        ]
        insert_from_json(
            petitions, columns=inai_json_fields, main_app='inai',
            main_model='Petition', main_key='inai_open_search')

        return Response(data, status=status.HTTP_201_CREATED)
