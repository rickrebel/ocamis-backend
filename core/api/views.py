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

"""class CatalogViewStig(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        campus_serializer = CampusSerializer(Campus.objects.all(), many=True)
        member_type_serializer = MemberTypeSerializer(
            MemberType.objects.all(), many=True)

        taining_serializer = TainingSerializer(
            Taining.objects.all(), many=True)
        officetype_serializer = OfficeTypeSerializer(
            OfficeType.objects.all(), many=True)
        sitetype_serializer = SiteTypeSerializer(
            SiteType.objects.all(), many=True)
        category_serializer = CategorySerializer(
            Category.objects.all(), many=True)
        status_serializer = StatusRegisterSerializer(
            StatusRegister.objects.all(), many=True)
        type_dep_serializer = TypeDependenceSimpleSerializer(
            TypeDependence.objects.all(), many=True)
        reasons_move_serializer = ReasonMoveSimpleSerializer(
            ReasonMove.objects.all(), many=True)

        data = {
            "campus": campus_serializer.data,
            "member_type": member_type_serializer.data,
            "taining": taining_serializer.data,
            "officetype": officetype_serializer.data,
            "sitetype": sitetype_serializer.data,
            "categories": category_serializer.data,
            "status_register": status_serializer.data,
            "type_dependence": type_dep_serializer.data,
            "reasons_move": reasons_move_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)"""
