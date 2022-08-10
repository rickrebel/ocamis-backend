# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
import unidecode

from inai.models import (
    FileControl, Petition, MonthEntity, PetitionMonth, PetitionBreak,
    ProcessFile, PetitionFileControl, DataFile)

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,)

from rest_framework.exceptions import (PermissionDenied, ValidationError)


class DataFileViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["get"], detail=True, url_path='explore')
    def explore(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()
        data = data_file.start_file_process(is_explore=True)
        #print(data["headers"])
        #print(data["structured_data"][:6])
        #new_serializer = serializers.DataFileSerializer(
        #    data_file)
        return Response(
            data, status=status.HTTP_201_CREATED)

