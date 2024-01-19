
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.mixins import (
    MultiSerializerListRetrieveMix as ListRetrieveView,
    MultiSerializerListCreateRetrieveUpdateMix as ListCreateRetrieveUpdateView)
from intl_medicine.api import serializers

from intl_medicine.models import Respondent, GroupAnswer


def data_response(respondent=None, group=None):
    if not respondent:
        next_group = GroupAnswer.objects\
            .filter(respondent__isnull=True, date_finished__isnull=True)\
            .order_by("?").first()
    else:
        next_group = create_group_answer(respondent)
    data = {"next_group": None, "respondent": None}
    if respondent:
        data["respondent"] = serializers.RespondentSerializer(respondent).data
    if next_group:
        data["next_group"] = serializers.GroupAnswerSerializer(next_group).data
    return Response(data=data, status=status.HTTP_200_OK)


def create_group_answer(respondent=None, group=None):
    from django.utils import timezone
    if not group and not respondent:
        raise Exception("No respondent or group provided")

    if not group:
        group = respondent.get_next_group()
        if not group:
            return None
    new_group_answer = GroupAnswer()
    new_group_answer.group = group
    new_group_answer.respondent = respondent
    new_group_answer.date_started = timezone.now()
    new_group_answer.save()
    return new_group_answer


class RespondentViewSet(ListCreateRetrieveUpdateView):
    queryset = Respondent.objects.all()
    serializer_class = serializers.RespondentSerializer
    permission_classes = [permissions.AllowAny]
    action_serializers = {
        "create": serializers.RespondentSerializer,
        "list": serializers.RespondentSerializer,
        "retrieve": serializers.RespondentSerializer,
        "next_group": serializers.RespondentSerializer,
    }

    def create(self, request, *args, **kwargs):
        import binascii
        import os

        print("request.data", request.data)
        respondent_data = request.data
        token = binascii.hexlify(os.urandom(20)).decode()
        print("token", token)
        new_respondent = Respondent()

        respondent_data["token"] = token
        serializer = self.get_serializer_class()(
            new_respondent, data=respondent_data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        respondent = serializer.instance
        return data_response(respondent)

    @action(detail=True, methods=["get"])
    def next_group(self, request, pk=None):
        respondent = self.get_object()
        return data_response(respondent)


class GroupAnswerViewSet(ListCreateRetrieveUpdateView):
    queryset = GroupAnswer.objects.all()
    serializer_class = serializers.GroupAnswerSimpleSerializer
    permission_classes = [permissions.AllowAny]
    action_serializers = {
        "list": serializers.GroupAnswerSimpleSerializer,
        "update": serializers.GroupAnswerSimpleSerializer,
        "retrieve": serializers.GroupAnswerSerializer,
    }

    def list(self, request, *args, **kwargs):
        # print("Estoy en el list")
        respondent_id = request.query_params.get("respondent_id", None)
        if respondent_id:
            self.queryset = self.queryset.filter(respondent_id=respondent_id)
        else:
            user = request.user
            if not user:
                return Response({"error": "No user provided"},
                                status=status.HTTP_400_BAD_REQUEST)
            if not user.is_superuser:
                return Response({"error": "User is not superuser"},
                                status=status.HTTP_400_BAD_REQUEST)
            self.queryset = self.queryset.filter(respondent__isnull=True)
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        from django.utils import timezone
        from intl_medicine.models import PrioritizedComponent

        group_answer = self.get_object()
        group_data = request.data
        components = request.data.pop("components", [])
        user = request.user
        respondent = group_answer.respondent
        if not respondent and not user:
            return Response(
                {"error": "No respondent or user provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # is_admin = False
        # if user:
        #     is_admin = user.is_superuser or user.is_staff
        group_data["date_finished"] = timezone.now()
        serializer = self.get_serializer_class()(group_answer, data=group_data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        for comp in components:
            pc_id = comp.pop("id", None)
            # print("comp", comp)
            if pc_id:
                new_prioritized = PrioritizedComponent.objects.get(id=pc_id)
            else:
                new_prioritized = PrioritizedComponent()
            # new_prioritized = PrioritizedComponent()
            # comp["group_answer"] = group_answer.id
            comp_ser = serializers.PrioritizedComponentSerializer(
                new_prioritized, data=comp)
            if not comp_ser.is_valid():
                return Response(
                    comp_ser.errors, status=status.HTTP_400_BAD_REQUEST
                )
            comp_ser.save()
        return data_response(respondent)
