# -*- coding: utf-8 -*-

from rest_framework import (permissions, status, views)
from rest_framework.response import Response

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction, 
    ParameterGroup)
from data_param.api.serializers import (
    DataGroupSimpleSerializer, CollectionSimpleSerializer,
    FinalFieldSimpleSerializer, DataTypeSimpleSerializer,
    CleanFunctionSimpleSerializer, ParameterGroupSimpleSerializer)

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason, DateBreak, Anomaly)
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer, NegativeReasonSimpleSerializer,
    DateBreakSimpleSerializer, AnomalySimpleSerializer)

from catalog.models import Entity
from catalog.api.serializers import EntitySerializer

from inai.models import FileControl
from inai.api.serializers import (
    FileControlFullSerializer)


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        #data = {}
        entities_query = Entity.objects.filter().prefetch_related(
            "institution", "state", "clues")
        file_control_query = FileControl.objects.all().prefetch_related(
            "data_group",
            "file_type",
            "columns",
            "petition_file_control",
            "petition_file_control__petition",
            "petition_file_control__petition",
            "petition_file_control__petition__petition_months",
            "petition_file_control__petition__petition_months__month_entity",
            "petition_file_control__data_files",
            "petition_file_control__data_files__origin_file",
        )
        final_fields_query = FinalField.objects.filter(dashboard_hide=False)

        data = {
            "file_controls": FileControlFullSerializer(
                file_control_query, many=True).data,
            "entities": EntitySerializer(entities_query, many=True).data,
            ## CATÁLOGOS DE PARÁMETROS:
            "data_groups": DataGroupSimpleSerializer(
                DataGroup.objects.all(), many=True).data,
            "collections": CollectionSimpleSerializer(
                Collection.objects.all(), many=True).data,
            "parameter_groups": ParameterGroupSimpleSerializer(
                ParameterGroup.objects.all(), many=True).data,
            "final_fields": FinalFieldSimpleSerializer(
                final_fields_query, many=True).data,
            ## CATÁLOGOS GENERALES:
            "data_types": DataTypeSimpleSerializer(
                DataType.objects.all(), many=True).data,
            "clean_functions": CleanFunctionSimpleSerializer(
                CleanFunction.objects.all(), many=True).data,
            "file_types": FileTypeSimpleSerializer(
                FileType.objects.all(), many=True).data,
            "status": StatusControlSimpleSerializer(
                StatusControl.objects.all(), many=True).data,
            "column_types": ColumnTypeSimpleSerializer(
                ColumnType.objects.all(), many=True).data,
            "negative_reasons": NegativeReasonSimpleSerializer(
                NegativeReason.objects.all(), many=True).data,
            "anomalies": AnomalySimpleSerializer(
                Anomaly.objects.all(), many=True).data,
            "date_breaks": DateBreakSimpleSerializer(
                DateBreak.objects.all(), many=True).data,
        }
        return Response(data)




class OpenDataVizView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        from category.models import Anomaly, StatusControl
        from data_param.models import CleanFunction
        from inai.models import (
            Petition, FileControl, MonthEntity, PetitionMonth)
        from catalog.models import Entity



        operability = {
            "ideal": {
                "formats": ["csv", "json", "txt"],
                "anomalies": [],
                "others": [],
            },
            "aceptable": {
                "formats": ["xls"],
                "anomalies": [
                    "code_headers",
                    "no_headers",
                    "hide_colums_tabs"
                ],
                "others": [],
            },
            "enhaced": {
                "formats": [],
                "anomalies": [
                    "different_tipe_tabs",
                    "internal_catalogue",
                    "hide_colums_tabs",
                    "no_valid_row_data",
                    "concatenated"
                    "same_group_data",
                    #solo para local:
                    "abasdf",
                ],
                "others": ["many_file_controls"],
            },
            "impeachable": {
                "formats": ["pdf", "word", "email", "other"],
                "anomalies": ["row_spaces"],
                "others": [],
            },
        }

        pilot = request.query_params.get("is_pilot", "false")
        is_pilot = pilot.lower() in ["si", "yes", "true"]

        all_entities = Entity.objects.filter(
            competent=True, vigencia=True)
        if is_pilot:
            all_entities = all_entities.filter(is_pilot=True)

        final_entities = []
        try:
            status_invalid = StatusControl.objects.get(
                name="mistake")
            petitions = petitions.exclude(
                status_petition=status_invalid)
        except Exception as e:
            status_invalid = None

        for entity in all_entities:
            final_entity = {
                "id": entity.id,
                "acronym": entity.acronym,
                "name": entity.name,
                "state": entity.state and entity.state.name,
                "clues": entity.clues and entity.clues.name,
                "entity_type": entity.entity_type,
            }
            #all_petitions = Petition.objects.filter(entity__in=all_entities)
            petitions = Petition.objects.filter(entity=entity)
            if status_invalid:
                petitions = petitions.exclude(status_petition=status_invalid)
            all_pets = []
            for petition in petitions:
                many_file_controls = False
                file_ctrls = FileControl.objects.filter(
                    petition_file_control__petition=petition).distinct()
                if file_ctrls.count() > 1:
                    many_file_controls = True
                try:
                    anomalies = Anomaly.objects.filter(
                        filecontrol__petition_file_control__petition=petition)
                    name_anomalies = anomalies\
                        .values_list("name", flat=True).distinct()
                    name_anomalies = list(anomalies)
                except Exception as e:
                    print(e)
                    name_anomalies = []
                file_formats = file_ctrls.filter(format_file__isnull=False)\
                    .values_list("format_file", flat=True)
                #if file_formats:
                #    print(file_formats)
                #glob_var = "many_file_controls"
                #print("FINAL", locals()[glob_var])
                status_data = petition.status_data and petition.status_data.name
                months = MonthEntity.objects.filter(
                    petitionmonth__petition=petition)
                final_status = None
                for (status, params) in operability.items():
                    if not set(params["formats"]).isdisjoint(set(file_formats)):
                        final_status = status
                    if not set(params["anomalies"]).isdisjoint(set(name_anomalies)):
                        final_status = status
                    for other in params["others"]:
                        if locals()[other]:
                            final_status = status
                if not status_data or (
                        status_data in ["no_data", "waiting", "pick_up"]):
                    final_status = "no_data"
                final_petition = {
                    "petition": petition.id,
                    "file_formats": file_formats,
                    "many_file_controls": many_file_controls,
                    #"anomalies": name_anomalies,
                    "final_status": final_status,
                    "file_ctrls_count": file_ctrls.count(),
                    "status_data": status_data,
                }
                all_months = []
                for month in months:
                    all_months.append(month.year_month)
                final_petition["year_months"] = all_months
                all_pets.append(final_petition)
            final_entities.append(final_entity)
            others_months = MonthEntity.objects.filter(
                petitionmonth__isnull=True, entity=entity)
            none_petition = {
                "petition": None,
                "file_formats": [],
                "many_file_controls": False,
                "file_ctrls_count": 0,
                "status_data": None,
                "final_status": "pending",
                "year_months": [month.year_month for month in others_months]
            }
            all_pets.append(none_petition)
            final_entity["petitions"] = all_pets

        #data = {"all_months": all_months}
        data = {"all_entities": final_entities}
        print("total months", MonthEntity.objects.all().count())
        print(data)
        return Response(data)




        quality = {
            "enough": {

            },
            "almost_enough":{

            },
            "not_enough":{

            },
        }

        
