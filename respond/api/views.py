from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from api.mixins import MultiSerializerModelViewSet, MultiSerializerCreateRetrieveMix as CreateRetrieveView, \
    MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix
from inai.models import Petition, PetitionFileControl
from respond.models import ReplyFile, DataFile, SheetFile
from . import serializers


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
        from storages.backends.s3boto3 import S3Boto3Storage
        from respond.models import get_path_with_petition
        petition_id = self.kwargs.get("petition_id")
        reply_file = request.data
        new_reply_file = ReplyFile()
        new_reply_file.petition_id = petition_id
        file_1 = request.FILES.get("file")

        # storage_name = "DEEP_ARCHIVE" if deep else "GLACIER_IR"
        if ".zip" in file_1.name or ".rar" in file_1.name:
            pass
        else:
            file = reply_file.pop("file")[0]
            params = {"object_parameters": {"StorageClass": "GLACIER_IR"}}
            boto_s3 = S3Boto3Storage(**params)
            petition = Petition.objects.get(id=petition_id)
            real_name = get_path_with_petition(petition, file.name, "reply")
            file_name = boto_s3.save(real_name, file, 255)
            new_reply_file.file = file_name

        serializer_proc_file = self.get_serializer_class()(
            new_reply_file, data=reply_file)

        if serializer_proc_file.is_valid():
            serializer_proc_file.save()
        else:
            return Response({"errors": serializer_proc_file.errors},
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


class AscertainableViewSet(CreateRetrieveView):
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
        pfc = PetitionFileControl.objects.get(id=petition_file_control_id)
        if pfc.file_control.real_provider:
            data_file["provider"] = pfc.file_control.real_provider_id
        else:
            agency_id = request.data.get("agency_id")
            agency = Agency.objects.get(id=agency_id)
            data_file["provider"] = agency.provider_id
        new_data_file = DataFile()

        serializer_data_file = self.get_serializer_class()(
            new_data_file, data=data_file)
        if serializer_data_file.is_valid():
            # control = serializer_data_file.save()
            # print("serializer_data_file", serializer_data_file)
            serializer_data_file.save()
        else:
            return Response({"errors": serializer_data_file.errors},
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
            return Response({"errors": serializer_data_file.errors},
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


class SheetFileViewSet(ListRetrieveUpdateMix):
    queryset = SheetFile.objects.all()
    serializer_class = serializers.SheetFileEditSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "update": serializers.SheetFileEditSerializer,
        "list": serializers.SheetFileSerializer,
    }

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
            return Response({"errors": serializer_sheet_file.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_sheet_file.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=["put"], detail=True, url_path='change_behavior')
    def change_behavior(self, request, **kwargs):
        from inai.api.views import get_related_months
        from respond.models import Behavior
        sheet_file = self.get_object()
        data = request.data
        new_behavior = data.get("behavior")
        new_behavior = Behavior.objects.get(name=new_behavior)
        old_behavior = sheet_file.behavior
        sheet_file.behavior = new_behavior
        is_merge_changed = new_behavior.is_merge != old_behavior.is_merge
        is_discarded_changed = new_behavior.is_discarded != old_behavior.is_discarded
        if new_behavior.is_discarded:
            sheet_file.duplicates_count = 0
            sheet_file.shared_count = 0
            sheet_file.self_repeated_count = 0
        sheet_file.save()
        if is_merge_changed or is_discarded_changed:
            if related_months := sheet_file.month_records.all():
                data_response = get_related_months(
                    all_related_months=related_months)
                return Response(data_response, status=status.HTTP_200_OK)
        return Response(
            {"behavior_counts": [], "drugs_summarize": {}, },
            status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False, url_path='massive_change_behavior')
    def massive_change_behavior(self, request, **kwargs):
        from inai.api.views import get_related_months
        from respond.models import Behavior
        data = request.data

        new_behavior = data.get("behavior")
        new_behavior_obj = Behavior.objects.get(name=new_behavior)

        sheet_files = SheetFile.objects \
            .filter(laps__rx_count__gt=0, laps__lap__gte=0)

        month_record_id = data.get("month_record_id")
        sheet_files_ids = data.get("sheet_files")
        behavior_group = data.get("behavior_group")
        if not sheet_files_ids and not month_record_id:
            return Response(
                {"error": "You must provide month_record_id or sheet_files"},
                status=status.HTTP_400_BAD_REQUEST)

        if month_record_id:
            sheet_files = sheet_files.filter(
                month_records__id__in=[month_record_id])
        if sheet_files_ids:
            sheet_files = sheet_files.filter(id__in=sheet_files_ids)
        if behavior_group:

            if behavior_group in ["invalid", "discarded"]:
                sheet_files = sheet_files.filter(behavior__is_discarded=True)
            else:
                sheet_files = sheet_files.exclude(behavior__is_discarded=True)
                if behavior_group == "dupli":
                    sheet_files = sheet_files.exclude(
                        duplicates_count=0, shared_count=0,
                        self_repeated_count=0)
                    # print("sheet_files", sheet_files)
                else:
                    sheet_files = sheet_files.filter(
                        duplicates_count=0, shared_count=0,
                        self_repeated_count=0)

        sheet_files = sheet_files.distinct()
        sheet_files_ids = list(sheet_files.values_list("id", flat=True))

        if new_behavior_obj.is_discarded:
            sheet_files.update(
                duplicates_count=0, shared_count=0, self_repeated_count=0)
        sheet_files.update(behavior=new_behavior_obj)
        data_response = get_related_months(sheet_files_ids=sheet_files_ids)
        return Response(data_response, status=status.HTTP_200_OK)
