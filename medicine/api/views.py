# -*- coding: utf-8 -*-
from . import serializers
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from django.db.models import Q

from medicine.models import (
    Component, Group, PresentationType,
    Presentation, Container)

from api.mixins import ListMix
from api.mixins import MultiSerializerListRetrieveMix
from core.api.views import StandardResultsSetPagination


class ComponentList(MultiSerializerListRetrieveMix):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ComponentSerializer
    queryset = Component.objects.all()
    action_serializers = {
        "retrieve": serializers.ComponentRetrieveSerializer,
        "priority": serializers.ComponentVizSerializer,
    }

    def list(self, request):
        from django.db.models import Q
        q = request.query_params.get("q")
        if q:
            q_list = [word.strip() for word in q.split(",") if word]
        else:
            q_list = None

        if q_list:

            first_word = q_list.pop()
            query_and = Q(name__icontains=first_word,
                          alias__icontains=first_word)
            query_or = Q(Q(name__icontains=first_word) |
                         Q(alias__icontains=first_word))
            for word in q_list:
                query_and |= Q(name__icontains=word,
                               alias__icontains=word)
                query_or |= Q(Q(name__icontains=word) |
                              Q(alias__icontains=word))

            queryset = Component.objects.filter(is_relevant=True)\
                .filter(query_and).distinct()

            if queryset.count() < 200:
                queryset_2 = Component.objects.filter(is_relevant=False)\
                    .filter(query_and).distinct()
                queryset = queryset.union(queryset_2)

            if queryset.count() < 200:
                queryset_3 = Component.objects.filter(is_relevant=True)\
                    .filter(query_or).distinct()
                queryset = queryset.union(queryset_3)

            if queryset.count() < 200:
                queryset_4 = Component.objects.filter(is_relevant=False)\
                    .filter(query_or).distinct()
                queryset = queryset.union(queryset_4)
        else:
            queryset = Component.objects.all()

        serializer = self.get_serializer_class()(
            # queryset.distinct()[:200], many=True)
            queryset.distinct().order_by("-frequency"), many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='key')
    def key(self, request, **kwargs):
        clave = request.query_params.get("clave")
        try:
            container = Container.objects.get(key=clave)
        except Container.DoesNotExist:
            raise NotFound({"errors": "No se encontro la clave: %s" % clave})
        serializer = serializers.ComponentRetrieveSerializer(
            container.presentation.component)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='priority')
    def priority(self, request, **kwargs):
        components = Component.objects\
            .filter(priority__lt=10)\
            .prefetch_related(
                "presentations",
                "presentations__containers",
                "presentations__groups"
            )\
            .order_by("priority")
        serializer = self.get_serializer_class()(components, many=True)
        return Response(serializer.data)


class GroupList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.GroupSerializer
    queryset = Group.objects.all()


class PresentationTypeList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PresentationTypeSerializer
    queryset = PresentationType.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(name__icontains=q) |
            Q(common_name__icontains=q) |
            Q(alias__icontains=q)
        ).distinct()


class PresentationList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PresentationSerializer
    queryset = Presentation.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(component__name__icontains=q) |
            Q(component__alias__icontains=q) |
            Q(component__presentations_raw__icontains=q) |
            Q(presentation_type__name__icontains=q) |
            Q(presentation_type__common_name__icontains=q) |
            Q(presentation_type__alias__icontains=q) |
            Q(description__icontains=q) |
            Q(presentation_type_raw__icontains=q) |
            Q(clave__icontains=q) |
            Q(official_name__icontains=q) |
            Q(official_attributes__icontains=q) |
            Q(short_attributes__icontains=q)
        ).distinct()


class ContainerList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.ContainerSerializer
    queryset = Container.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(name__icontains=q) |
            Q(key__icontains=q) |
            Q(short_name__icontains=q)
        ).distinct()
