# -*- coding: utf-8 -*-
from rest_framework.pagination import PageNumberPagination

from geo.models import State, Institution, Alliances, Disease
from geo.api.serializers import (
    StateSerializer, InstitutionSerializer, AlliancesSerializer,
    DiseaseSerializer)
from rest_framework import (permissions, views)
from rest_framework.response import Response
# --------Paginacion-----------------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 1000
# -----------------------------------------------------------------------------


class HeavyResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
# -----------------------------------------------------------------------------


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        data = {
            "states": StateSerializer(
                State.objects.all(), many=True).data,
            "institutions": InstitutionSerializer(
                Institution.objects.all().order_by("relevance"),
                many=True).data,
            "alliances": AlliancesSerializer(
                Alliances.objects.all().order_by("name"),
                many=True, context={"request": request}).data,
            "diseases": DiseaseSerializer(
                Disease.objects.all().order_by("name"),
                many=True, context={"request": request}).data
        }
        return Response(data)
