# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action

from inai.models import (
    Petition, SheetFile, PetitionBreak,
    ReplyFile, PetitionFileControl, DataFile, EntityMonth, TableFile)
from rest_framework.pagination import PageNumberPagination
from api.mixins import (
    MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,
    MultiSerializerModelViewSet)
from rest_framework.exceptions import (PermissionDenied)


class NormalResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


# -----------------------------------------------------------------------------


class PetitionViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "create": serializers.PetitionEditSerializer,
        "retrieve": serializers.PetitionFullSerializer,
        "update": serializers.PetitionEditSerializer,
        # "list": serializers.PetitionFilterSerializer,
        # "change_months": serializers.PetitionEditSerializer,
    }

    def create(self, request, **kwargs):
        # self.check_permissions(request)
        data_petition = request.data
        new_petition = Petition()
        petition = None
        range_months = data_petition.pop('range_months', [])
        petition_reasons = data_petition.pop('petition_reasons', [])
        petition_breaks = data_petition.pop('build_petition_breaks', [])
        agency = data_petition.pop('agency', [])
        data_petition["agency"] = agency["id"]

        serializer_pet = self.get_serializer_class()(
            new_petition, data=data_petition)
        if serializer_pet.is_valid():
            petition = serializer_pet.save()
        else:
            return Response({ "errors": serializer_pet.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        data_petition["petition"] = petition.id

        entity_months = EntityMonth.objects.filter(
            entity=petition.agency.entity,
            year_month__gte=range_months[0],
            year_month__lte=range_months[1])

        # for entity_month in entity_months:
        #     PetitionMonth.objects.create(
        #         petition=petition, entity_month=entity_month)
        entity_months_ids = entity_months.values_list('id', flat=True)
        petition.entity_months.set(entity_months_ids)

        for pet_break in petition_breaks:
            petition_break = PetitionBreak()
            petition_break.petition = petition

            serializer_pb = serializers.PetitionBreakSerializer(
                petition_break, data=pet_break)
            if serializer_pb.is_valid():
                serializer_pb.save()
            else:
                print(serializer_pb.errors)

        new_serializer = serializers.PetitionFullSerializer(
            petition, context={'request': request})
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):
        from category.models import NegativeReason
        from inai.models import PetitionNegativeReason

        petition = self.get_object()
        data_petition = request.data

        other_reasons = data_petition.pop('other_reasons', [])
        main_reason = data_petition.pop('main_reason', None)
        petition_breaks = data_petition.pop('break_dates', [])

        serializer_petition = self.get_serializer_class()(
            petition, data=data_petition)
        if serializer_petition.is_valid():
            # control = serializer_data_file.save()
            serializer_petition.save()
        else:
            return Response({ "errors": serializer_petition.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        for negative in other_reasons:
            negative_obj = NegativeReason.objects.get(name=negative)
            petition_negative_reason, created = PetitionNegativeReason.objects \
                .get_or_create(petition=petition,
                               negative_reason=negative_obj, is_main=False)

        if main_reason:
            negative_obj = NegativeReason.objects.get(name=main_reason)
            petition_negative_reason, created = PetitionNegativeReason.objects \
                .get_or_create(petition=petition,
                               negative_reason=negative_obj, is_main=True)

        for pet_break in petition_breaks:
            if "id" in pet_break:
                petition_break = PetitionBreak.objects.get(id=pet_break["id"])
            else:
                petition_break = PetitionBreak()
                petition_break.petition = petition

            serializer_pb = serializers.PetitionBreakSerializer(
                petition_break, data=pet_break)
            if serializer_pb.is_valid():
                serializer_pb.save()
            else:
                print(serializer_pb.errors)

        petition_updated = Petition.objects.get(id=petition.id)
        new_serializer = serializers.PetitionFullSerializer(
            petition_updated, context={ 'request': request })
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

        # return Response(
        #    serializer_petition.data, status=status.HTTP_201_CREATED)

    @action(methods=["get"], detail=False, url_path='filter')
    def filter(self, request, **kwargs):
        from data_param.models import FileControl
        from inai.models import Petition
        from data_param.api.serializers import FileControlSemiFullSerializer
        from data_param.api.views import build_common_filters

        import json
        limiters = request.query_params.get("limiters", None)
        limiters = json.loads(limiters)

        petitions = Petition.objects.all().prefetch_related(
            # "petition_months",
            "entity_months",
            "file_controls",
            "break_dates",
            "negative_reasons",
            "negative_reasons__negative_reason",
            "file_controls",
            "agency",
        ).order_by("agency__acronym", "folio_petition")
        total_count = 0
        available_filters = [
            {"name": "status_petition", "field": "status_petition_id"},
            {"name": "status_data", "field": "status_data_id"},
            {"name": "status_complain", "field": "status_complain_id"},
        ]
        if limiters:
            all_filters = build_common_filters(limiters, available_filters)
            if limiters.get("selected_year"):
                if limiters.get("selected_month"):
                    # all_filters["petition_months__month_agency__year_month"] =\
                    #     f"{limiters.get('selected_year')}-{limiters.get('selected_month')}"
                    all_filters["entity_months__year_month"] =\
                        f"{limiters.get('selected_year')}-{limiters.get('selected_month')}"
                else:
                    # all_filters["petition_months__month_agency__year_month__icontains"] =\
                    #     limiters.get("selected_year")
                    all_filters["entity_months__year_month__icontains"] =\
                        limiters.get("selected_year")
            if all_filters:
                petitions = petitions.filter(**all_filters).distinct()
            total_count = petitions.count()
            page_size = limiters.get("page_size", 40)
            page = limiters.get("page", 1) - 1
            petitions = petitions[page * page_size:(page + 1) * page_size]

        if not total_count:
            total_count = petitions.count()
        # serializer =
        serializer = serializers.PetitionSemiFullSerializer(
            petitions, many=True, context={'request': request})
        related_controls = FileControl.objects.filter(
            petition_file_control__petition__in=petitions).distinct()
        serializer_controls = FileControlSemiFullSerializer(
            related_controls, many=True, context={'request': request})
        data = {
            "petitions": serializer.data,
            "file_controls": serializer_controls.data,
            "total_count": total_count,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def change_months(self, request, **kwargs):
        limiters = request.data.get("limiters")
        print(limiters)
        # limiters = json.loads(limiters)

        petition = self.get_object()
        # current_pet_months = PetitionMonth.objects.filter(petition=petition)
        # current_pet_months.exclude(
        #     month_agency__year_month__gte=limiters[0],
        #     month_agency__year_month__lte=limiters[1],
        # ).delete()
        new_entity_month = EntityMonth.objects.filter(
            entity=petition.agency.entity,
            year_month__gte=limiters[0], year_month__lte=limiters[1])
        # for mon_ent in new_entity_month:
        #     PetitionMonth.objects.get_or_create(
        #         petition=petition, entity_month=mon_ent)
        petition.entity_months.set(new_entity_month)

        # final_pet_months = PetitionMonth.objects.filter(petition=petition)
        # new_serializer = serializers.PetitionMonthSerializer(
        #     final_pet_months, many=True)
        new_serializer = serializers.EntityMonthSimpleSerializer(
            petition.entity_months, many=True)
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)


class PetitionList(views.APIView):
    permission_classes = (permissions.AllowAny,)
    pagination_class = NormalResultsSetPagination

    def get(self, request):
        status_petition = request.query_params.get("status_petition")
        # state_inegi_code = request.query_params.get("estado")

        serial = serializers.PetitionFilterSerializer()


class ReplyFileViewSet(MultiSerializerModelViewSet):
    queryset = ReplyFile.objects.all()
    serializer_class = serializers.ReplyFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.ReplyFileSerializer,
        "retrieve": serializers.ReplyFileSerializer,
        "create": serializers.ReplyFileSerializer,
        "delete": serializers.ReplyFileEditSerializer,
    }

    def get_queryset(self):
        if "petition_id" in self.kwargs:
            return ReplyFile.objects.filter(
                petition_id=self.kwargs["petition_id"])
        return ReplyFile.objects.all()

    def create(self, request, **kwargs):
        petition_id = self.kwargs.get("petition_id")
        reply_file = request.data
        new_reply_file = ReplyFile()
        new_reply_file.petition_id = petition_id

        # serializer = serializers.ReplyFileEditSerializer(data=request.data)
        serializer_proc_file = self.get_serializer_class()(
            new_reply_file, data=reply_file)

        if serializer_proc_file.is_valid():
            serializer_proc_file.save()
        else:
            return Response({ "errors": serializer_proc_file.errors },
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_proc_file.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, **kwargs):
        petition_id = self.kwargs.get("petition_id")
        try:
            petition = Petition.objects.get(id=petition_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        reply_file = self.get_object()
        self.perform_destroy(reply_file)
        return Response(status=status.HTTP_200_OK)


class PetitionFileControlViewSet(CreateRetrievView):
    queryset = PetitionFileControl.objects.all()
    serializer_class = serializers.PetitionFileControlFullSerializer
    permission_classes = [permissions.IsAdminUser]
    action_serializers = {
        "list": serializers.PetitionFileControlFullSerializer,
        "retrieve": serializers.PetitionFileControlFullSerializer,
        "create": serializers.PetitionFileControlCreateSerializer,
        "delete": serializers.PetitionFileControlFullSerializer,
    }

    def get_queryset(self):
        # if "petition_id" in self.kwargs:
        #    return PetitionFileControl.objects.filter(
        #        petition=self.kwargs["petition_id"])
        return PetitionFileControl.objects.all()

    def create(self, request, petition_id=False):

        petition_file_control = request.data
        new_pet_file_ctrl = PetitionFileControl()

        serializer_pet_file_ctrl = self.get_serializer_class()(
            new_pet_file_ctrl, data=petition_file_control)

        if serializer_pet_file_ctrl.is_valid():
            serializer_pet_file_ctrl.save()
        else:
            return Response({ "errors": serializer_pet_file_ctrl.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(
            serializer_pet_file_ctrl.data, status=status.HTTP_201_CREATED)

    @action(methods=["put"], detail=True, url_path='move_massive')
    def move_massive(self, request, **kwargs):
        from inai.api.views_aws import move_and_duplicate
        from inai.models import DataFile

        petition_file_control = self.get_object()
        petition = petition_file_control.petition
        files_id = request.data.get("files")
        data_files = DataFile.objects.filter(
            petition_file_control=petition_file_control,
            id__in=files_id)

        return move_and_duplicate(data_files, petition, request)


class AscertainableViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
        "retrieve": serializers.DataFileEditSerializer,
        "create": serializers.DataFileSerializer,
        "update": serializers.DataFileEditSerializer,
        "delete": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        if "petition_file_control_id" in self.kwargs:
            return DataFile.objects.filter(
                petition_file_control_id=self.kwargs["petition_file_control_id"])
        return DataFile.objects.all()

    def create(self, request, petition_file_control_id=False, **kwargs):
        from geo.models import Agency
        data_file = request.data
        new_data_file = DataFile()
        agency_id = request.data.get("agency_id")
        agency = Agency.objects.get(id=agency_id)
        data_file["entity"] = agency.entity_id

        serializer_data_file = self.get_serializer_class()(
            new_data_file, data=data_file)
        if serializer_data_file.is_valid():
            # control = serializer_data_file.save()
            # print("serializer_data_file", serializer_data_file)
            serializer_data_file.save()
        else:
            return Response({ "errors": serializer_data_file.errors },
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_data_file.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):

        data_file = self.get_object()
        data = request.data
        # new_data_file = DataFile()

        serializer_data_file = self.get_serializer_class()(
            data_file, data=data)
        if serializer_data_file.is_valid():
            # control = serializer_data_file.save()
            serializer_data_file.save()
        else:
            return Response({ "errors": serializer_data_file.errors },
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_data_file.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def destroy(self, request, **kwargs):
        petition_file_control_id = self.kwargs.get("petition_file_control_id")
        try:
            petition_file_control = PetitionFileControl.objects \
                .get(id=petition_file_control_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data_file = self.get_object()
        self.perform_destroy(data_file)
        return Response(status=status.HTTP_200_OK)


class EntityMonthViewSet(CreateRetrievView):
    queryset = EntityMonth.objects.all()
    serializer_class = serializers.EntityMonthSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "retrieve": serializers.EntityMonthSerializer,
    }

    def retrieve(self, request, **kwargs):
        from inai.api.serializers import (SheetFileMonthSerializer)
        from inai.models import CrossingSheet
        entity_month = self.get_object()
        sheet_files = SheetFile.objects.filter(
            laps__table_files__entity_week__entity_month=entity_month)\
            .distinct()
        serializer_sheet_files = SheetFileMonthSerializer(
            sheet_files, many=True)
        crossing_sheets_1 = CrossingSheet.objects.filter(
            sheet_file_1__in=sheet_files)
        crossing_sheets_2 = CrossingSheet.objects.filter(
            sheet_file_2__in=sheet_files)
        all_crossing_sheets = crossing_sheets_1 | crossing_sheets_2
        if all_crossing_sheets.filter(entity_month__isnull=True).exists():
            all_crossing_sheets = all_crossing_sheets.filter(
                entity_month__isnull=True)

        all_related_sheets = set()
        for crossing_sheet in all_crossing_sheets:
            all_related_sheets.add(crossing_sheet.sheet_file_1_id)
            all_related_sheets.add(crossing_sheet.sheet_file_2_id)
        related_sheet_files = SheetFile.objects.filter(
            id__in=list(all_related_sheets))
        serializer_related_files = SheetFileMonthSerializer(
            related_sheet_files, many=True)

        serializer_crossing_sheets = serializers.CrossingSheetSimpleSerializer(
            all_crossing_sheets, many=True)
        return Response({
            "sheet_files": serializer_sheet_files.data,
            "related_sheets": serializer_related_files.data,
            "crossing_sheets": serializer_crossing_sheets.data
        })

    @action(detail=True, methods=["post"], url_path="change_behavior")
    def change_behavior(self, request, **kwargs):
        entity_month = self.get_object()

        behavior = request.data.get("behavior")
        sheet_files = SheetFile.objects\
            .filter(
                laps__table_files__entity_week__entity_month=entity_month,
                duplicates_count=0,
                shared_count=0,
                rx_count__gt=0,
                laps__lap=0)\
            .distinct()
        sheet_files.update(behavior_id=behavior)
        return Response(status=status.HTTP_200_OK)


class SheetFileViewSet(ListRetrieveUpdateMix):
    queryset = SheetFile.objects.all()
    serializer_class = serializers.SheetFileEditSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "update": serializers.SheetFileEditSerializer,
    }

    def get_queryset(self):
        return SheetFile.objects.all()

    def update(self, request, **kwargs):

        sheet_file = self.get_object()
        data = request.data
        # new_data_file = DataFile()

        serializer_sheet_file = self.get_serializer_class()(
            sheet_file, data=data)
        if serializer_sheet_file.is_valid():
            # control = serializer_data_file.save()
            serializer_sheet_file.save()
        else:
            return Response({ "errors": serializer_sheet_file.errors },
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_sheet_file.data, status=status.HTTP_206_PARTIAL_CONTENT)
