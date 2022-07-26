# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)

"""from files_rows.models import FileControl
from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)



class FileControlViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.FileControlSerializer
    queryset = FileControl.objects.all().prefetch_related(
                "columns",
                "columns__column_type",
                "columns__data_type",
                "columns__column_tranformations",
                "columns__column_tranformations__clean_function",
                "columns__final_field",
                "columns__final_field__collection",
            )
    
    action_serializers = {
        "list": serializers.FileControlSerializer,
        "retrieve": serializers.FileControlFullSerializer,
    }

    def get(self, request):
        print("ESTOY EN GET")
        file_contol = self.get_object()
        serializer = serializers.FileControlFullSerializer(
            file_contol, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()
"""