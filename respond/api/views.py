from rest_framework import permissions, status
from rest_framework.response import Response

import respond.api
from api.mixins import MultiSerializerModelViewSet, MultiSerializerCreateRetrieveMix as CreateRetrieveView, \
    MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix
from inai.models import Petition, PetitionFileControl
from respond.models import ReplyFile, DataFile, SheetFile


class ReplyFileViewSet(MultiSerializerModelViewSet):
    queryset = ReplyFile.objects.all()
    serializer_class = respond.api.serializers.ReplyFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": respond.api.serializers.ReplyFileSerializer,
        "retrieve": respond.api.serializers.ReplyFileSerializer,
        "create": respond.api.serializers.ReplyFileSerializer,
        "delete": respond.api.serializers.ReplyFileEditSerializer,
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


class AscertainableViewSet(CreateRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = respond.api.serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": respond.api.serializers.DataFileSerializer,
        "retrieve": respond.api.serializers.DataFileEditSerializer,
        "create": respond.api.serializers.DataFileSerializer,
        "update": respond.api.serializers.DataFileEditSerializer,
        "delete": respond.api.serializers.DataFileSerializer,
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
        if pfc.file_control.real_entity:
            data_file["entity"] = pfc.file_control.real_entity_id
        else:
            agency_id = request.data.get("agency_id")
            agency = Agency.objects.get(id=agency_id)
            data_file["entity"] = agency.entity_id
        new_data_file = DataFile()

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


class SheetFileViewSet(ListRetrieveUpdateMix):
    queryset = SheetFile.objects.all()
    serializer_class = respond.api.serializers.SheetFileEditSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "update": respond.api.serializers.SheetFileEditSerializer,
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
