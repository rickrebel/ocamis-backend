# -*- coding: utf-8 -*-
import respond.api.serializers
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, status)
from rest_framework.decorators import action

from inai.models import (
    Petition, PetitionBreak,
    PetitionFileControl, MonthRecord)
from respond.models import SheetFile, CrossingSheet
from rest_framework.pagination import PageNumberPagination
from api.mixins import (
    MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrieveView)


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

    def retrieve(self, request, **kwargs):
        from task.models import ClickHistory
        petition = self.get_object()
        ClickHistory.objects.create(petition=petition, user=request.user)
        serializer = self.get_serializer_class()(petition)
        return Response(serializer.data)

    def create(self, request, **kwargs):
        # self.check_permissions(request)
        data_petition = request.data
        new_petition = Petition()
        # petition_reasons = data_petition.pop('petition_reasons', [])
        range_months = data_petition.pop('range_months', [])
        petition_breaks = data_petition.pop('build_petition_breaks', [])
        print("data_petition", data_petition)

        serializer_pet = self.get_serializer_class()(
            new_petition, data=data_petition)
        if serializer_pet.is_valid():
            petition = serializer_pet.save()
        else:
            return Response({"errors": serializer_pet.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        data_petition["petition"] = petition.id

        month_records = MonthRecord.objects.filter(
            provider=petition.agency.provider,
            year_month__gte=range_months[0],
            year_month__lte=range_months[1])

        # for month_record in month_records:
        #     PetitionMonth.objects.create(
        #         petition=petition, month_record=month_record)
        month_records_ids = month_records.values_list('id', flat=True)
        petition.month_records.set(month_records_ids)

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
            "month_records",
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
            {"name": "invalid_reason", "field": "invalid_reason_id"},
        ]
        if limiters:
            all_filters = build_common_filters(limiters, available_filters)

            if limiters.get("selected_year"):
                if limiters.get("selected_month"):
                    # all_filters["petition_months__month_agency__year_month"] =\
                    #     f"{limiters.get('selected_year')}-{limiters.get('selected_month')}"
                    all_filters["month_records__year_month"] =\
                        f"{limiters.get('selected_year')}-{limiters.get('selected_month')}"
                else:
                    # all_filters["petition_months__month_agency__year_month__icontains"] =\
                    #     limiters.get("selected_year")
                    all_filters["month_records__year_month__icontains"] =\
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
        new_month_record = MonthRecord.objects.filter(
            provider=petition.agency.provider,
            year_month__gte=limiters[0], year_month__lte=limiters[1])
        # for mon_ent in new_entity_month:
        #     PetitionMonth.objects.get_or_create(
        #         petition=petition, month_record=mon_ent)
        petition.month_records.set(new_month_record)

        # final_pet_months = PetitionMonth.objects.filter(petition=petition)
        # new_serializer = serializers.PetitionMonthSerializer(
        #     final_pet_months, many=True)
        new_serializer = serializers.MonthRecordSimpleSerializer(
            petition.month_records, many=True)
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)


class PetitionFileControlViewSet(CreateRetrieveView):
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
        from respond.api.views_aws import move_and_duplicate
        from inai.models import DataFile

        petition_file_control = self.get_object()
        petition = petition_file_control.petition
        files_id = request.data.get("files")
        data_files = DataFile.objects.filter(
            petition_file_control=petition_file_control,
            id__in=files_id)

        return move_and_duplicate(data_files, petition, request)


class MonthRecordViewSet(CreateRetrieveView):
    queryset = MonthRecord.objects.all()
    serializer_class = serializers.MonthRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "retrieve": serializers.MonthRecordSerializer,
    }

    def retrieve(self, request, **kwargs):
        from respond.api.serializers import SheetFileMonthSerializer
        from task.models import ClickHistory
        month_record = self.get_object()
        ClickHistory.objects.create(
            month_record=month_record, user=request.user)
        sheet_files = month_record.sheet_files.all() \
            .prefetch_related("data_file", "data_file__petition_file_control")
        # sheet_files = SheetFile.objects.filter(
        #     laps__table_files__week_record__month_record=month_record)\
        #     .distinct()
        serializer_sheet_files = SheetFileMonthSerializer(
            sheet_files, many=True)
        crossing_sheets_1 = CrossingSheet.objects.filter(
            sheet_file_1__in=sheet_files)
        crossing_sheets_2 = CrossingSheet.objects.filter(
            sheet_file_2__in=sheet_files)
        all_crossing_sheets = crossing_sheets_1 | crossing_sheets_2
        if all_crossing_sheets.filter(month_record__isnull=False).exists():
            all_crossing_sheets = all_crossing_sheets.filter(
                month_record__isnull=False)

        all_related_sheets = set()
        for crossing_sheet in all_crossing_sheets:
            all_related_sheets.add(crossing_sheet.sheet_file_1_id)
            all_related_sheets.add(crossing_sheet.sheet_file_2_id)
        for initial_sheet in sheet_files:
            if initial_sheet.id in all_related_sheets:
                all_related_sheets.remove(initial_sheet.id)
        related_sheet_files = SheetFile.objects\
            .filter(id__in=list(all_related_sheets)) \
            .prefetch_related("data_file", "data_file__petition_file_control")
        serializer_related_files = SheetFileMonthSerializer(
            related_sheet_files, many=True)

        serializer_crossing_sheets = respond.api.serializers.CrossingSheetSimpleSerializer(
            all_crossing_sheets, many=True)
        return Response({
            "sheet_files": serializer_sheet_files.data,
            "related_sheets": serializer_related_files.data,
            "crossing_sheets": serializer_crossing_sheets.data
        })

    @action(detail=True, methods=["post"], url_path="change_behavior")
    def change_behavior(self, request, **kwargs):
        month_record = self.get_object()

        behavior = request.data.get("behavior")
        for_all = request.data.get("all", False)
        sheet_files = month_record.sheet_files.filter(
            laps__rx_count__gt=0,
            laps__lap=0).distinct()
        # sheet_files = SheetFile.objects.filter(
        #     laps__table_files__week_record__month_record=month_record,
        #     rx_count__gt=0,
        #     laps__lap=0)
        if for_all:
            sheet_files = sheet_files.exclude(
                duplicates_count=0,
                shared_count=0,
            ).distinct()
        else:
            sheet_files = sheet_files.filter(
                duplicates_count=0,
                shared_count=0,
            ).distinct()
        sheet_files.update(behavior_id=behavior)
        return Response(status=status.HTTP_200_OK)


