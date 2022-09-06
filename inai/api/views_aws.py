# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
import unidecode

from inai.models import DataFile, NameColumn

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,)

from rest_framework.exceptions import (PermissionDenied, ValidationError)


class DataFileViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["get"], detail=True, url_path='explore')
    def explore(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()
        data = data_file.start_file_process(is_explore=True)
        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)
        
        def textNormalizer(text):
            import re
            import unidecode
            final_text = text.upper().strip()
            final_text = unidecode.unidecode(final_text)
            final_text = re.sub(r'[^A-Z][DE|DEL][^A-Z]', ' ', final_text)
            final_text = re.sub(r' +', ' ', final_text)
            final_text = re.sub(r'[^A-Z]', '', final_text)
            return final_text
        
        valid_fields = [
            "name_in_data", "column_type", "final_field", "parameter_group",
            "data_type"]
        try:
            headers = data["headers"]
            complex_headers = []
            file_control = data_file.petition_file_control.file_control
            data_groups = [file_control.data_group.name, 'catalogs']
            all_name_columns = NameColumn.objects\
                .filter(
                    final_field__isnull=False,
                    name_in_data__isnull=False,
                    final_field__parameter_group__data_group__in=data_groups,
                )\
                .values(*valid_fields)
            
            #.exclude(name_in_data__startswith="_")

            final_names = {}
            for name_col in all_name_columns:
                standar_name = textNormalizer(name_col["name_in_data"])
                unique_name = (
                    f'{standar_name}-{name_col["final_field"]}-'
                    f'{name_col["parameter_group"]}')
                if final_names.get(standar_name, False):
                    if not final_names[standar_name]["valid"]:
                        continue
                    elif final_names[standar_name]["unique_name"] != unique_name:
                        final_names[standar_name]["valid"] = False
                    continue
                else:
                    base_dict = {
                        "valid": True,
                        "unique_name": unique_name,
                        "standar_name": standar_name
                    }
                    base_dict.update(name_col)
                    final_names[standar_name] = base_dict
            final_names = {
                name: vals for name, vals in final_names.items()
                    if vals["valid"]}
            for (position, header) in enumerate(headers, start=1):
                std_header = textNormalizer(header)
                base_dict = {"position_in_data": position}
                if final_names.get(std_header, False):
                    vals = final_names[std_header]
                    base_dict.update({field: vals[field] for field in valid_fields})
                base_dict["name_in_data"] = header
                complex_headers.append(base_dict)
            data["complex_headers"] = complex_headers
        except Exception as e:
            print("HUBO UN ERRORZASO")
            print(e)
        #print(data["structured_data"][:6])
        return Response(
            data, status=status.HTTP_201_CREATED)


class OpenDataInaiViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
        "create": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all()

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
                "insert": True,
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

