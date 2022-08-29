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
        from data_param.models import CleanFunction, FinalField
        from inai.models import (
            Petition, FileControl, MonthEntity, PetitionMonth)
        from catalog.models import Entity

        data_groups = ["Recetas desglosadas", "Almacén"]
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
        qualities = ["not_enough", "enough", "almost_enough", "not_enough"]

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
                status_data = petition.status_data and petition.status_data.name
                current_months = MonthEntity.objects.filter(
                        petitionmonth__petition=petition).distinct()\
                    .values_list("year_month", flat=True)
                final_petition = {
                    "petition": petition.id,
                    "folio": petition.folio_petition,
                    "status_data": status_data,
                    "year_months": current_months,
                }
                for data_group in data_groups:
                    many_file_controls = False
                    file_ctrls = FileControl.objects.filter(
                        petition_file_control__petition=petition,
                        data_group__public_name=data_group).distinct()
                    if file_ctrls.count() > 1:
                        many_file_controls = True
                    try:
                        anomalies = Anomaly.objects.filter(
                            filecontrol__in=file_ctrls)
                        name_anomalies = anomalies\
                            .values_list("name", flat=True).distinct()
                        name_anomalies = list(anomalies)
                    except Exception as e:
                        print(e)
                        name_anomalies = []
                    file_formats = file_ctrls.filter(format_file__isnull=False)\
                        .values_list("format_file", flat=True)
                    final_quality = None
                    for (quality, params) in operability.items():
                        if not set(params["formats"]).isdisjoint(set(file_formats)):
                            final_quality = quality
                        if not set(params["anomalies"]).isdisjoint(set(name_anomalies)):
                            final_quality = quality
                        for other in params["others"]:
                            if locals()[other]:
                                final_quality = quality
                    if not status_data or (
                            status_data in ["no_data", "waiting", "pick_up"]):
                        final_quality = "no_data"
                    final_petition[data_group] = {
                        "file_formats": file_formats,
                        "many_file_controls": many_file_controls,
                        "final_quality": final_quality,
                        "file_ctrls_count": file_ctrls.count(),
                        "status_data": status_data,
                    }
                    if data_group != "Recetas desglosadas":
                        continue
                    clues = 0
                    formula = 0
                    droug = 0
                    for file_ctrl in file_ctrls:
                        final_fields = FinalField.objects.filter(
                                namecolumn__file_control=file_ctrl,
                                need_for_viz=True).distinct()\
                            .values_list("collection__model_name", "name")
                        has_clues = ("CLUES", "clues") in final_fields
                        has_name = ("CLUES", "name") in final_fields
                        if has_clues and clues < 2:
                            clues = 1
                        elif (has_clues or has_name) and clues < 3:
                            clues = 2
                        else:
                            clues = 3
                        emision = (("Prescription", "fecha_emision") in final_fields or
                            ("Prescription", "fecha_consulta") in final_fields)
                        entrega = ("Prescription", "fecha_entrega") in final_fields
                        folio = ("Prescription", "folio_documento") in final_fields
                        if folio and emision and entrega and formula < 2:
                            formula = 1
                        elif folio and (emision or entrega) and formula < 3:
                            formula = 2
                        else:
                            formula = 3
                        official_key = ("Container", "key2") in final_fields
                        prescrita = ("Droug", "cantidad_prescrita") in final_fields
                        entregada = ("Droug", "cantidad_entregada") in final_fields
                        own_key = ("Container", "_own_key") in final_fields
                        other_names = (("Droug", "droug_name") in final_fields or
                            ("Presentation", "description") in final_fields or
                            ("Container", "name") in final_fields)
                        if prescrita and entregada:
                            if official_key and droug < 2:
                                droug = 1
                            elif (official_key or others_names or own_key) and droug < 3:
                                droug = 2
                        if not droug:
                            droug = 3
                    
                    final_petition[data_group]["clues"] = qualities[clues]
                    final_petition[data_group]["formula"] = qualities[formula]
                    final_petition[data_group]["droug"] = qualities[droug]                            
                all_pets.append(final_petition)
            final_entities.append(final_entity)
            #others_months = MonthEntity.objects.filter(
            #    petitionmonth__isnull=True, entity=entity)
            all_months = MonthEntity.objects.filter(entity=entity)\
                .distinct().values_list("year_month", flat=True)
            none_petition = {
                "petition": None,
                "file_formats": [],
                "many_file_controls": False,
                "file_ctrls_count": 0,
                "status_data": None,
                "final_quality": "pending",
                #"year_months": [month.year_month for month in others_months]
                "all_months": all_months
            }
            all_pets.append(none_petition)
            final_entity["petitions"] = all_pets

        #data = {"all_months": all_months}
        data = {"all_entities": final_entities}
        #print("total months", MonthEntity.objects.all().count())
        #print(data)
        return Response(data)
