# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)

from inai.models import (
    FileControl, Petition, MonthEntity, PetitionMonth, PetitionBreak)
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
        file_control = self.get_object()
        serializer = serializers.FileControlFullSerializer(
            file_control, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()


class PetitionViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.FileControlSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "create": serializers.PetitionEditSerializer,
        #"update": serializers.FileControlFullSerializer,
    }

    def create(self, request, **kwargs):
        #self.check_permissions(request)
        data_petition = request.data
        new_petition = Petition()
        petition = None
        range_months = data_petition.pop('range_months', [])
        petition_breaks = data_petition.pop('build_petition_breaks', [])
        supplies_items = data_petition.pop('supplies', [])
        entity = data_petition.pop('entity', [])
        data_petition["entity"] = entity["id"]
        
        serializer_pet = self.get_serializer_class()(
            new_petition, data=data_petition)
        if serializer_pet.is_valid():
            petition = serializer_pet.save()
        else:
            return Response({"errors": serializer_pet.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        data_petition["petition"] = petition.id

        month_entitites = MonthEntity.objects.filter(
            entity=petition.entity, 
            year_month__gte=range_months[0],
            year_month__lte=range_months[1])

        for month_entity in month_entitites:
            PetitionMonth.objects.create(
                petition=petition, month_entity=month_entity)

        print(petition)
        print("petition_breaks", petition_breaks)
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
