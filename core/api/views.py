# -*- coding: utf-8 -*-

from rest_framework import (permissions, status, views)
from rest_framework.response import Response

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction,
    ParameterGroup, FileControl)
from data_param.api.serializers import (
    DataGroupSimpleSerializer, CollectionSimpleSerializer,
    FinalFieldSimpleSerializer, DataTypeSimpleSerializer,
    CleanFunctionSimpleSerializer, ParameterGroupSimpleSerializer, )
from inai.api.serializers import (
    FileControlFullSerializer, BehaviorSimpleSerializer)
from inai.models import Behavior

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat)
from transparency.models import Anomaly, TransparencyIndex
from classify_task.models import StatusTask, TaskFunction, Stage
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer, NegativeReasonSimpleSerializer,
    DateBreakSimpleSerializer, AnomalySimpleSerializer,
    InvalidReasonSimpleSerializer, FileFormatSimpleSerializer,
    TransparencyIndexSimpleSerializer, TransparencyLevelSimpleSerializer,
    TransparencyIndexSerializer,)
from task.api.serializers import (
    StatusTaskSimpleSerializer, TaskFunctionSerializer, StageSimpleSerializer)

from geo.models import Agency, Entity
from geo.api.serializers import AgencySerializer, EntitySerializer


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        #data = {}
        agencies_query = Agency.objects.filter().prefetch_related(
            "institution", "state", "clues")
        final_fields_query = FinalField.objects.filter(dashboard_hide=False)

        data = {
            "agencies": AgencySerializer(agencies_query, many=True).data,
            "entities": EntitySerializer(Entity.objects.all(), many=True).data,
            ## CATÁLOGOS DE PARÁMETROS:
            "data_groups": DataGroupSimpleSerializer(
                DataGroup.objects.all(), many=True).data,
            "collections": CollectionSimpleSerializer(
                Collection.objects.all(), many=True).data,
            "parameter_groups": ParameterGroupSimpleSerializer(
                ParameterGroup.objects.all(), many=True).data,
            "final_fields": FinalFieldSimpleSerializer(
                final_fields_query, many=True).data,
            ## TASKS:
            "status_tasks": StatusTaskSimpleSerializer(
                StatusTask.objects.all(), many=True).data,
            "task_functions": TaskFunctionSerializer(
                TaskFunction.objects.all(), many=True).data,
            "stages": StageSimpleSerializer(
                Stage.objects.all(), many=True).data,

            ## CATÁLOGOS GENERALES:
            "data_types": DataTypeSimpleSerializer(
                DataType.objects.all(), many=True).data,
            "clean_functions": CleanFunctionSimpleSerializer(
                CleanFunction.objects.all(), many=True).data,
            "behaviors": BehaviorSimpleSerializer(
                Behavior.objects.all(), many=True).data,
            "file_types": FileTypeSimpleSerializer(
                FileType.objects.all(), many=True).data,
            "status": StatusControlSimpleSerializer(
                StatusControl.objects.all(), many=True).data,
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
