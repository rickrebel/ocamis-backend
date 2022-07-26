# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)

from files_rows.models import GroupFile
from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)



class GroupFileViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.GroupFileSerializer
    queryset = GroupFile.objects.all().prefetch_related(
                "columns",
                "columns__column_type",
                "columns__type_data",
                "columns__column_tranformations",
                "columns__column_tranformations__clean_function",
                "columns__final_field",
                "columns__final_field__collection",
            )
    
    action_serializers = {
        "list": serializers.GroupFileSerializer,
        "retrieve": serializers.GroupFileFullSerializer,
    }

    def get(self, request):
        print("ESTOY EN GET")
        group_file = self.get_object()
        serializer = serializers.GroupFileFullSerializer(
            group_file, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()

