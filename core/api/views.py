# -*- coding: utf-8 -*-

from rest_framework import (permissions, status, views)
from rest_framework.response import Response

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction, 
    ParameterGroup)
from data_param.api.serializers import (
    DataGroupSimpleSerializer, CollectionSimpleSerializer,
    FinalFieldSimpleSerializer, DataTypeSimpleSerializer,
    CleanFunctionSimpleSerializer, ParameterGroupSimpleSerializer,)

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason,
    DateBreak, Anomaly, InvalidReason, FileFormat,
    TransparencyIndex, TransparencyLevel, StatusTask)
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer, NegativeReasonSimpleSerializer,
    DateBreakSimpleSerializer, AnomalySimpleSerializer,
    InvalidReasonSimpleSerializer, FileFormatSimpleSerializer,
    TransparencyIndexSimpleSerializer, TransparencyLevelSimpleSerializer,
    TransparencyIndexSerializer, StatusTaskSimpleSerializer,)

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
            "columns",
            "columns__column_transformations",
            "petition_file_control",
            "petition_file_control__data_files",
            "petition_file_control__data_files__origin_file",
        )
        final_fields_query = FinalField.objects.filter(dashboard_hide=False)

        data = {
            #"file_controls": FileControlFullSerializer(
            #    file_control_query, many=True).data,
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
            "status_tasks": StatusTaskSimpleSerializer(
                StatusTask.objects.all(), many=True).data,
            "column_types": ColumnTypeSimpleSerializer(
                ColumnType.objects.all(), many=True).data,
            "negative_reasons": NegativeReasonSimpleSerializer(
                NegativeReason.objects.all(), many=True).data,
            "invalid_reasons": InvalidReasonSimpleSerializer(
                InvalidReason.objects.all(), many=True).data,
            "anomalies": AnomalySimpleSerializer(
                Anomaly.objects.all(), many=True).data,
            "file_formats": FileFormatSimpleSerializer(
                FileFormat.objects.all(), many=True).data,
            "date_breaks": DateBreakSimpleSerializer(
                DateBreak.objects.all(), many=True).data,
        }
        return Response(data)


class CatalogViz(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        #data = {}
        final_fields_query = FinalField.objects.filter(need_for_viz=True)
        indices_query = TransparencyIndex.objects.all()\
            .prefetch_related(
                "levels", "levels__anomalies", "levels__file_formats")

        data = {
            ## CATÁLOGOS DE PARÁMETROS:
            "parameter_groups": ParameterGroupSimpleSerializer(
                ParameterGroup.objects.all(), many=True).data,
            "final_fields": FinalFieldSimpleSerializer(
                final_fields_query, many=True).data,
            ## CATÁLOGOS DE TRANSPARENCIA:
            "indices": TransparencyIndexSerializer(
                indices_query, many=True).data,
            #"levels": TransparencyLevelSimpleSerializer(
            #    TransparencyLevel.objects.all(), many=True).data,
            ## CATÁLOGOS GENERALES:
            "negative_reasons": NegativeReasonSimpleSerializer(
                NegativeReason.objects.all(), many=True).data,
            "invalid_reasons": InvalidReasonSimpleSerializer(
                InvalidReason.objects.all(), many=True).data,
            "anomalies": AnomalySimpleSerializer(
                Anomaly.objects.all(), many=True).data,
            "file_formats": FileFormatSimpleSerializer(
                FileFormat.objects.all(), many=True).data,
        }
        return Response(data)
