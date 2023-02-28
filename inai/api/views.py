# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action

from task.views import build_task_params, comprobate_status

from inai.models import (
    FileControl, Petition, MonthEntity, PetitionMonth, PetitionBreak,
    ProcessFile, PetitionFileControl, DataFile, Transformation)
from rest_framework.pagination import PageNumberPagination
from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,
    MultiSerializerModelViewSet)
from rest_framework.exceptions import (PermissionDenied, ValidationError)


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
        entity = data_petition.pop('entity', [])
        data_petition["entity"] = entity["id"]

        serializer_pet = self.get_serializer_class()(
            new_petition, data=data_petition)
        if serializer_pet.is_valid():
            petition = serializer_pet.save()
        else:
            return Response({ "errors": serializer_pet.errors },
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
            petition, context={ 'request': request })
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):
        from rest_framework.exceptions import (NotFound)
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

    @action(methods=["post"], detail=True)
    def change_months(self, request, **kwargs):
        import json
        if not request.user.is_staff:
            raise PermissionDenied()
        limiters = request.data.get("limiters")
        print(limiters)
        # limiters = json.loads(limiters)

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


class PetitionList(views.APIView):
    permission_classes = (permissions.AllowAny,)
    pagination_class = NormalResultsSetPagination

    def get(self, request):
        status_petition = request.query_params.get("status_petition")
        # state_inegi_code = request.query_params.get("estado")

        serial = serializers.PetitionFilterSerializer()


class ProcessFileViewSet(MultiSerializerModelViewSet):
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
            # ParseError,  #400
            NotFound)  # 404

        process_file = request.data
        new_process_file = ProcessFile()
        new_process_file.petition_id = petition_id

        # serializer = serializers.ProcessFileEditSerializer(data=request.data)
        serializer_proc_file = self.get_serializer_class()(
            new_process_file, data=process_file)

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
        process_file = self.get_object()
        self.perform_destroy(process_file)
        return Response(status=status.HTTP_200_OK)


class FileControlViewSet(MultiSerializerModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.FileControlSerializer
    queryset = FileControl.objects.all().prefetch_related(
        "data_group",
        "columns",
        "file_transformations",
        "columns__column_transformations",
        "petition_file_control",
        "petition_file_control__data_files",
        "petition_file_control__data_files__origin_file",
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["show_institution"] = True
        # context["show_institution"] = self.kwargs['customer_id']
        # context["query_params"] = self.request.query_params
        return context

    action_serializers = {
        "list": serializers.FileControlFullSerializer,
        "retrieve": serializers.FileControlFullSerializer,
        "create": serializers.FileControlSerializer,
        "post": serializers.FileControlSerializer,
        "update": serializers.FileControlSerializer,
    }

    def get(self, request):
        # print("ESTOY EN GET")
        file_control = self.get_object()
        serializer = serializers.FileControlFullSerializer(
            file_control, context={ 'request': request })
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()

    def create(self, request, **kwargs):
        # print("ESTOY EN CREATE")
        data_file_control = request.data
        new_file_control = FileControl()

        petition_id = data_file_control.pop('petition_id', None)

        serializer_ctrl = self.get_serializer_class()(
            new_file_control, data=data_file_control)
        if serializer_ctrl.is_valid():
            file_control = serializer_ctrl.save()
        else:
            return Response({ "errors": serializer_ctrl.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        if petition_id:
            new_pet_file_ctrl = PetitionFileControl.objects.create(
                petition_id=petition_id, file_control=file_control)

            new_serializer = serializers.PetitionFileControlDeepSerializer(
                new_pet_file_ctrl, context={ 'request': request })
            return Response(
                new_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"errors": "No se ha podido crear el control de archivo"},
                status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, **kwargs):
        file_control = self.get_object()
        data = request.data

        transformations = data.pop('transformations', [])
        serializer_file_control = self.get_serializer_class()(
            file_control, data=data)
        if serializer_file_control.is_valid():
            serializer_file_control.save()
        else:
            return Response({ "errors": serializer_file_control.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        actual_id_tranformations = []
        for transf_item in transformations:
            transformation = Transformation()
            transform_ser = serializers.TransformationEditSerializer(
                transformation, data=transf_item)
            if transform_ser.is_valid():
                tranform = transform_ser.save()
                actual_id_tranformations.append(tranform.id)
        Transformation.objects.filter(file_control=file_control) \
            .exclude(id__in=actual_id_tranformations).delete()

        new_file_control = FileControl.objects.get(id=file_control.id)
        new_serializer = serializers.FileControlFullSerializer(
            new_file_control)
        return Response(
            new_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

        # return Response(
        #    serializer_file_control.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=["post"], detail=True, url_path='columns')
    def columns(self, request, **kwargs):
        from inai.models import NameColumn, FileControl
        import json
        if not request.user.is_staff:
            raise PermissionDenied()
        columns_items = request.data.get("columns")
        file_control = self.get_object()
        # limiters = json.loads(limiters)

        actual_id_columns = []
        for (order, column_item) in enumerate(columns_items, start=1):
            column_id = column_item.get("id", False)
            transformations = column_item.pop('transformations', [])
            print("TRANSFORMATIONS", transformations)
            column_item["seq"] = order
            if column_item.get("name_in_data"):
                column_item["name_in_data"] = column_item["name_in_data"]\
                    .strip().upper()
            if column_id:
                # print("sí tenngo column", column_item["id"])
                column = NameColumn.objects.filter(
                    id=column_id, file_control=file_control).first()
                if not column:
                    print("no continúo")
                    continue
            else:
                # print("Es nuevooo")
                column = NameColumn()
                column.file_control = file_control

            column_serializer = serializers.NameColumnEditSerializer(
                column, data=column_item)
            if column_serializer.is_valid():
                print("es válido")
                column = column_serializer.save()
                actual_id_columns.append(column.id)
                actual_id_tranformations = []
                for transf_item in transformations:
                    transformation = Transformation()
                    transf_item["name_column"] = column.id
                    transform_ser = serializers.TransformationEditSerializer(
                        transformation, data=transf_item)
                    if transform_ser.is_valid():
                        print("transf válido")
                        tranform = transform_ser.save()
                        actual_id_tranformations.append(tranform.id)
                        print("transf_id", tranform.id)
                    else:
                        print("NO ES VALIDO", transform_ser.errors)
                Transformation.objects.filter(name_column=column) \
                    .exclude(id__in=actual_id_tranformations).delete()
            else:
                print("no es válido")
                print(column_serializer.errors)
        NameColumn.objects.filter(file_control=file_control) \
            .exclude(id__in=actual_id_columns).delete()

        new_file_control = FileControl.objects.get(id=file_control.id)
        new_serializer = serializers.FileControlFullSerializer(
            new_file_control)
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["get"], detail=True, url_path='link_orphans')
    def link_orphans(self, request, **kwargs):
        from inai.api.common import send_response

        file_control = self.get_object()
        petition = file_control.petition_file_control.petition
        orphan_files = DataFile.objects.filter(
            petition_file_control__petition=petition,
            petition_file_control__file_control__data_group__name="orphan",
        )
        if orphan_files.exists():
            key_task, task_params = build_task_params(
                file_control, "link_orphans", request)
            new_tasks, new_errors = petition.find_matches_in_children(
                orphan_files, current_file_ctrl=file_control.id,
                task_params=task_params)
            if len(new_tasks) == 0 and key_task:
                key_task.status_task_id = "finished"
                key_task.save()
            return send_response(petition, task=key_task, errors=new_errors)
        else:
            return Response(
                { "errors": ["No hay archivos en grupos huérfanos"] },
                status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["put"], detail=True, url_path='massive_action')
    def massive_action(self, request, **kwargs):

        file_control = self.get_object()
        status_req = request.data.get("status", { })
        status_id = status_req.get("id", False)
        status_name = status_req.get("name", False)
        all_data_files = DataFile.objects.filter(
            petition_file_control__file_control=file_control,
            status_process_id=status_id)
        method = status_req.get("addl_params", { }).get("next_step", { }).get("method", False)
        if method == "buildExploreDataFile" or method == "countFile":
            key_task, task_params = build_task_params(
                file_control, "massive_explore", request, subgroup=status_name)
            all_tasks = []
            all_errors = []

            for data_file in all_data_files[:50]:
                curr_kwargs = {
                    "after_if_empty": "find_coincidences_from_aws",
                    "all_tasks": all_tasks,
                }
                all_tasks, new_errors, data_file = data_file.get_sample_data(
                    task_params, **curr_kwargs)
                if not data_file:
                    continue
                task_params["models"] = [data_file]
                if method == "buildExploreDataFile":
                    process_error = "explore_fail"
                    data_file, saved, errors = data_file.find_coincidences()
                    if not saved and not errors:
                        errors = ["No coincide con el formato del archivo 1"]
                else:
                    process_error = "counting_failed"
                    all_tasks, errors, data_file = data_file.every_has_total_rows(
                        task_params)
                    if data_file:
                        data_rows = data_file.count_file_rows()
                        errors = data_rows.get("errors", [])
                if errors:
                    all_errors.extend(errors)
                    data_file.save_errors(errors, process_error)


            data = {
                "errors": all_errors,
                "file_control": serializers.FileControlFullSerializer(
                    file_control).data,
            }
            comprobate_status(key_task, errors=all_errors, new_tasks=all_tasks)
            data["new_task"] = key_task.id
            return Response(data, status=status.HTTP_200_OK)
            # elif method == 'countFile':

        # print("STATUS", status_req)

        return Response({"errors": ["No se encontró el método"]},
                        status=status.HTTP_400_BAD_REQUEST)


class PetitionFileControlViewSet(CreateRetrievView):
    queryset = PetitionFileControl.objects.all()
    serializer_class = serializers.PetitionFileControlFullSerializer
    permission_classes = [permissions.IsAuthenticated]
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
        from rest_framework.exceptions import (
            # ParseError,  #400
            NotFound)  # 404

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
        if not request.user.is_staff:
            raise PermissionDenied()

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
        from rest_framework.exceptions import (
            # ParseError,  #400
            NotFound)  # 404

        data_file = request.data
        new_data_file = DataFile()

        serializer_data_file = self.get_serializer_class()(
            new_data_file, data=data_file)
        if serializer_data_file.is_valid():
            # control = serializer_data_file.save()
            serializer_data_file.save()
        else:
            return Response({ "errors": serializer_data_file.errors },
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            serializer_data_file.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):
        from rest_framework.exceptions import (
            # ParseError,  #400
            NotFound)  # 404

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
