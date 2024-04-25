# -*- coding: utf-8 -*-

from rest_framework import (permissions, status, views)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction,
    ParameterGroup, FileControl)
from data_param.api.serializers import (
    DataGroupSimpleSerializer, CollectionSimpleSerializer,
    FinalFieldSimpleSerializer, DataTypeSimpleSerializer,
    CleanFunctionSimpleSerializer, ParameterGroupSimpleSerializer, )

from inai.models import RequestTemplate
from inai.api.serializers import RequestTemplateSerializer

from respond.api.serializers import BehaviorSimpleSerializer
from respond.models import Behavior

from transparency.models import Anomaly, TransparencyIndex

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat)
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer, NegativeReasonSimpleSerializer,
    DateBreakSimpleSerializer, AnomalySimpleSerializer,
    InvalidReasonSimpleSerializer, FileFormatSimpleSerializer,
    TransparencyIndexSerializer,)

from classify_task.models import StatusTask, TaskFunction, Stage
from task.api.serializers import (
    StatusTaskSimpleSerializer, TaskFunctionSerializer, StageSimpleSerializer)

from geo.models import Agency, Provider
from geo.api.serializers import (
    AgencySerializer, ProviderSerializer, ProviderCatSerializer)


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        from task.models import OFFLINE_TYPES
        # data = {}
        agencies_query = Agency.objects.filter().prefetch_related(
            "institution", "state", "clues")
        providers_query = Provider.objects.all().prefetch_related(
            "institution", "state", "ent_clues", "cut_offs")
        final_fields_query = FinalField.objects.filter(dashboard_hide=False)
        last_template = RequestTemplate.objects.filter(provider__isnull=True)\
            .first()


        data = {
            "agencies": AgencySerializer(agencies_query, many=True).data,
            "providers": ProviderCatSerializer(providers_query, many=True).data,
            # CATÁLOGOS DE PARÁMETROS:
            "data_groups": DataGroupSimpleSerializer(
                DataGroup.objects.all(), many=True).data,
            "collections": CollectionSimpleSerializer(
                Collection.objects.all(), many=True).data,
            "parameter_groups": ParameterGroupSimpleSerializer(
                ParameterGroup.objects.all(), many=True).data,
            "final_fields": FinalFieldSimpleSerializer(
                final_fields_query, many=True).data,
            # TASKS:
            "status_tasks": StatusTaskSimpleSerializer(
                StatusTask.objects.all(), many=True).data,
            "task_functions": TaskFunctionSerializer(
                TaskFunction.objects.all(), many=True).data,
            "stages": StageSimpleSerializer(
                Stage.objects.all(), many=True).data,

            # CATÁLOGOS GENERALES:
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
            "offline_types": {k: v for k, v in OFFLINE_TYPES},
            "last_request_template": RequestTemplateSerializer(
                last_template).data,
        }
        return Response(data)


class CatalogViz(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        # data = {}
        final_fields_query = FinalField.objects.filter(need_for_viz=True)
        indices_query = TransparencyIndex.objects.all()\
            .prefetch_related(
                "levels", "levels__anomalies", "levels__file_formats")

        data = {
            # CATÁLOGOS DE PARÁMETROS:
            "parameter_groups": ParameterGroupSimpleSerializer(
                ParameterGroup.objects.all(), many=True).data,
            "final_fields": FinalFieldSimpleSerializer(
                final_fields_query, many=True).data,
            # CATÁLOGOS DE TRANSPARENCIA:
            "indices": TransparencyIndexSerializer(
                indices_query, many=True).data,
            # "levels": TransparencyLevelSimpleSerializer(
            #    TransparencyLevel.objects.all(), many=True).data,
            # CATÁLOGOS GENERALES:
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


class CatalogShortageViz(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        from medicine.api.serializers import (
            ComponentVizAllSerializer, GroupSerializer)
        from medicine.models import Component, Group

        components = Component.objects\
            .filter(priority__lt=10)\
            .order_by("-frequency")

        data = {
            # CATÁLOGOS GENERALES:
            "components": ComponentVizAllSerializer(
                components, many=True).data,
            "groups": GroupSerializer(
                Group.objects.all(), many=True).data,
        }
        return Response(data)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 1000


class HeavyResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
