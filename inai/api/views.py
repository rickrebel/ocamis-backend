# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action

from inai.models import (
    FileControl, Petition, MonthEntity, PetitionMonth, PetitionBreak,
    ProcessFile, PetitionFileControl, DataFile)
from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,)
from rest_framework.exceptions import (PermissionDenied, ValidationError)


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["show_institution"] = True
        #context["show_institution"] = self.kwargs['customer_id']
        #context["query_params"] = self.request.query_params
        return context

    action_serializers = {
        "list": serializers.FileControlSerializer,
        "retrieve": serializers.FileControlFullSerializer,
        "create": serializers.FileControlSerializer,
        "post": serializers.FileControlSerializer,
        #"update": serializers.FileControlEditSerializer,
    }

    def get(self, request):
        print("ESTOY EN GET")
        file_control = self.get_object()
        serializer = serializers.FileControlFullSerializer(
            file_control, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()

    def create(self, request, **kwargs):
        print("ESTOY EN CREATE")
        data_file_control = request.data
        new_file_control = FileControl()

        petition_id = data_file_control.pop('petition_id', None)
        
        serializer_ctrl = self.get_serializer_class()(
            new_file_control, data=data_file_control)
        if serializer_ctrl.is_valid():
            file_control = serializer_ctrl.save()
        else:
            return Response({"errors": serializer_ctrl.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        if petition_id:
            new_pet_file_ctrl = PetitionFileControl.objects.create(
                petition_id=petition_id, file_control=file_control)

        new_serializer = serializers.PetitionFileControlDeepSerializer(
            new_pet_file_ctrl, context={'request': request})
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

        #return Response(
        #    serializer_ctrl.data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, url_path='columns')
    def columns(self, request, **kwargs):
        from inai.models import NameColumn, FileControl
        import json
        if not request.user.is_staff:
            raise PermissionDenied()
        columns_items = request.data.get("columns")
        file_control = self.get_object()
        #limiters = json.loads(limiters)

        actual_id_columns = []
        for column_item in columns_items:
            if "id" in column_item:
                print("sí tenngo column", column_item["id"])
                column = NameColumn.objects.filter(
                    id=column_item["id"], file_control=file_control).first()
                if not column:
                    print("no continúo")
                    continue
            else:
                print("Es nuevooo")
                column = NameColumn()
                column.file_control = file_control

            column_supp = serializers.NameColumnEditSerializer(
                column, data=column_item)
            if column_supp.is_valid():
                print("es válido")
                column = column_supp.save()
                actual_id_columns.append(column.id)
            else:
                print(column_supp.errors)
        NameColumn.objects.filter(file_control=file_control)\
            .exclude(id__in=actual_id_columns).delete()

        new_file_control = FileControl.objects.get(id=file_control.id)
        new_serializer = serializers.FileControlFullSerializer(
            new_file_control)
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)


class PetitionViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.FileControlSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "create": serializers.PetitionEditSerializer,
        "update": serializers.PetitionEditSerializer,
    }

    def create(self, request, **kwargs):
        #self.check_permissions(request)
        data_petition = request.data
        new_petition = Petition()
        petition = None
        range_months = data_petition.pop('range_months', [])
        petition_reasons = data_petition.pop('petition_reasons', [])
        petition_breaks = data_petition.pop('build_petition_breaks', [])
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
        from rest_framework.exceptions import (NotFound) 
        from category.models import NegativeReason
        from inai.models import PetitionNegativeReason

        petition = self.get_object()
        data = request.data

        other_reasons = data.pop('other_reasons', [])
        main_reason = data.pop('main_reason', None)
        
        serializer_petition = self.get_serializer_class()(
            petition, data=data)
        if serializer_petition.is_valid():
            #control = serializer_data_file.save()
            serializer_petition.save()
        else:
            return Response({"errors": serializer_petition.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        for negative in other_reasons:
            negative_obj = NegativeReason.objects.get(name=negative)            
            petition_negative_reason, created = PetitionNegativeReason.objects\
                .get_or_create(petition=petition, 
                    negative_reason = negative_obj, is_main=False)

        if main_reason:
            negative_obj = NegativeReason.objects.get(name=main_reason)            
            petition_negative_reason, created = PetitionNegativeReason.objects\
                .get_or_create(petition=petition,
                    negative_reason = negative_obj, is_main=True)

        return Response(
            serializer_petition.data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, url_path='change_months')
    def change_months(self, request, **kwargs):
        import json
        if not request.user.is_staff:
            raise PermissionDenied()
        limiters = request.data.get("limiters")
        print(limiters)
        #limiters = json.loads(limiters)

        petition = self.get_object()
        current_pet_months = PetitionMonth.objects.filter(petition=petition)
        current_pet_months.exclude(
            month_entity__year_month__gte=limiters[0],
            month_entity__year_month__lte=limiters[1],
            ).delete()
        new_month_entities = MonthEntity.objects.filter(
            entity=petition.entity,
            year_month__gte=limiters[0], year_month__lte=limiters[1])
        for mon_ent in new_month_entities:
            PetitionMonth.objects.get_or_create(
                petition=petition, month_entity=mon_ent)

        final_pet_monts = PetitionMonth.objects.filter(
            petition=petition)
        new_serializer = serializers.PetitionMonthSerializer(
            final_pet_monts, many=True)
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)


class ProcessFileViewSet(CreateRetrievView):
    queryset = ProcessFile.objects.all()
    serializer_class = serializers.ProcessFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.ProcessFileSerializer,
        "retrieve": serializers.ProcessFileSerializer,
        "create": serializers.ProcessFileSerializer,
        "delete": serializers.ProcessFileEditSerializer,
    }

    def get_queryset(self):
        if "petition_id" in self.kwargs:
            return ProcessFile.objects.filter(
                petition=self.kwargs["petition_id"])
        return ProcessFile.objects.all()

    def create(self, request, petition_id=False):
        from rest_framework.exceptions import (
            #ParseError,  #400
            NotFound)  # 404
        
        process_file = request.data
        new_process_file = DataFile()

        #serializer = serializers.ProcessFileEditSerializer(data=request.data)
        serializer_proc_file = self.get_serializer_class()(
            new_process_file, data=process_file)

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
        process_file = self.get_object()
        self.perform_destroy(process_file)
        return Response(status=status.HTTP_200_OK)


class PetitionFileControlViewSet(CreateRetrievView):
    queryset = PetitionFileControl.objects.all()
    serializer_class = serializers.PetitionFileControlSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.PetitionFileControlSerializer,
        "retrieve": serializers.PetitionFileControlSerializer,
        "create": serializers.PetitionFileControlSerializer,
        "delete": serializers.PetitionFileControlSerializer,
    }

    def get_queryset(self):
        #if "petition_id" in self.kwargs:
        #    return PetitionFileControl.objects.filter(
        #        petition=self.kwargs["petition_id"])
        return PetitionFileControl.objects.all()

    def create(self, request, petition_id=False):
        from rest_framework.exceptions import (
            #ParseError,  #400
            NotFound)  # 404
        
        petition_file_control = request.data
        new_pet_file_ctrl = PetitionFileControl()

        serializer_pet_file_ctrl = self.get_serializer_class()(
            new_pet_file_ctrl, data=petition_file_control)

        if serializer_pet_file_ctrl.is_valid():
            serializer_pet_file_ctrl.save()
        else:
            return Response({"errors": serializer_pet_file_ctrl.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(
            serializer_pet_file_ctrl.data, status=status.HTTP_201_CREATED)


class AscertainableViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
        "retrieve": serializers.DataFileSimpleSerializer,
        "create": serializers.DataFileSerializer,
        "update": serializers.DataFileEditSerializer,
        "delete": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        if "petition_file_control_id" in self.kwargs:
            return DataFile.objects.filter(
                petition_file_control_id=self.kwargs["petition_file_control_id"])
        return DataFile.objects.all()

    def create(self, request, petition_file_control_id=False):
        from rest_framework.exceptions import (
            #ParseError,  #400
            NotFound)  # 404

        data_file = request.data
        new_data_file = DataFile()

        serializer_data_file = self.get_serializer_class()(
            new_data_file, data=data_file)
        if serializer_data_file.is_valid():
            #control = serializer_data_file.save()
            serializer_data_file.save()
        else:
            return Response({"errors": serializer_data_file.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_data_file.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):
        from rest_framework.exceptions import (
            #ParseError,  #400
            NotFound)  # 404

        data_file = self.get_object()
        data = request.data
        #new_data_file = DataFile()

        serializer_data_file = self.get_serializer_class()(
            data_file, data=data)
        if serializer_data_file.is_valid():
            #control = serializer_data_file.save()
            serializer_data_file.save()
        else:
            return Response({"errors": serializer_data_file.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_data_file.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, **kwargs):
        petition_file_control_id = self.kwargs.get("petition_file_control_id")
        try:
            petition_file_control = PetitionFileControl.objects\
                .get(id=petition_file_control_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data_file = self.get_object()
        self.perform_destroy(data_file)
        return Response(status=status.HTTP_200_OK)

