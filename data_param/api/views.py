from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination


from api.mixins import MultiSerializerModelViewSet
from inai.api.serializers import (
    PetitionSemiFullSerializer, PetitionFileControlDeepSerializer,
    FileControlFullSerializer, TransformationEditSerializer,
    NameColumnEditSerializer)
from inai.models import PetitionFileControl, DataFile
from task.views import build_task_params, comprobate_status
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, status)

from ..models import FileControl, Transformation, NameColumn


class HeavyResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def build_common_filters(limiters, available_filters):
    final_filters = {}
    for filter_item in available_filters:
        if limiters.get(filter_item["name"]):
            final_filters[filter_item["field"]] = \
                limiters.get(filter_item["name"])
    if limiters.get("has_notes"):
        final_filters["notes__isnull"] = not limiters.get("has_notes")
    if limiters.get("status_task") or limiters.get("has_task"):
        final_filters["id__in"] = limiters.get("related_ids", [])
    if limiters.get("entity_type"):
        if limiters.get("entity_type") == 'Hospital Federal':
            final_filters["entity__clues__isnull"] = False
        elif limiters.get("entity_type") == 'Estatal':
            final_filters["entity__state__isnull"] = False
        else:
            final_filters["entity__clues__isnull"] = True
            final_filters["entity__state__isnull"] = True
    return final_filters


class FileControlViewSet(MultiSerializerModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.FileControlSerializer
    pagination_class = HeavyResultsSetPagination
    queryset = FileControl.objects.all().prefetch_related(
        "data_group",
        "columns",
        "columns__column_transformations",
        "file_transformations",
        "petition_file_control",
        "petition_file_control__data_files",
        # "petition_file_control__data_files__origin_file",
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["show_institution"] = True
        # context["show_institution"] = self.kwargs['customer_id']
        # context["query_params"] = self.request.query_params
        return context

    action_serializers = {
        "list": FileControlFullSerializer,
        "retrieve": FileControlFullSerializer,
        "create": serializers.FileControlSerializer,
        "post": serializers.FileControlSerializer,
        "update": serializers.FileControlSerializer,
        "filter": serializers.FileControlSemiFullSerializer,
    }

    def get_queryset(self):
        request = self.request
        status_register = request.query_params.get('status_register', None)
        controls = FileControl.objects.all().prefetch_related(
            "data_group",
            "columns",
            "columns__column_transformations",
            "file_transformations",
            "petition_file_control",
            "petition_file_control__data_files",
            # "petition_file_control__data_files__origin_file",
        )
        if status_register:
            controls = controls.filter(status_register_id=status_register)
        return controls

    def get(self, request):
        # print("ESTOY EN GET")
        file_control = self.get_object()
        serializer = FileControlFullSerializer(
            file_control, context={ 'request': request })
        return Response(serializer.data, status=status.HTTP_200_OK)

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

            new_serializer = PetitionFileControlDeepSerializer(
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

        serializer_file_control = self.get_serializer_class()(
            file_control, data=data)
        if serializer_file_control.is_valid():
            serializer_file_control.save()
        else:
            return Response({ "errors": serializer_file_control.errors },
                            status=status.HTTP_400_BAD_REQUEST)

        transformations = data.pop('transformations', None)
        if transformations is not None:
            actual_id_tranformations = []
            for transf_item in transformations:
                transformation = Transformation()
                transform_ser = TransformationEditSerializer(
                    transformation, data=transf_item)
                if transform_ser.is_valid():
                    tranform = transform_ser.save()
                    actual_id_tranformations.append(tranform.id)
            Transformation.objects.filter(file_control=file_control) \
                .exclude(id__in=actual_id_tranformations).delete()

        new_file_control = FileControl.objects.get(id=file_control.id)
        new_serializer = FileControlFullSerializer(
            new_file_control)
        return Response(
            new_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

        # return Response(
        #    serializer_file_control.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=["get"], detail=False, url_path='filter')
    def filter(self, request, **kwargs):
        from data_param.models import FileControl
        from inai.models import Petition
        import json
        limiters = request.query_params.get("limiters", None)
        limiters = json.loads(limiters)
        controls = FileControl.objects.all().prefetch_related(
            "data_group",
            "columns",
            "columns__column_transformations",
            "entity",
        ).order_by("data_group__name", "entity__acronym", "name")
        total_count = 0
        available_filters = [
            {"name": "status_register", "field": "status_register_id"},
            {"name": "data_group", "field": "data_group_id"},
            {"name": "file_format", "field": "file_format_id"},
        ]
        if limiters:
            all_filters = build_common_filters(limiters, available_filters)
            if all_filters:
                controls = controls.filter(**all_filters).distinct()
            total_count = controls.count()
            page_size = limiters.get("page_size", 40)
            page = limiters.get("page", 1) - 1
            controls = controls[page * page_size:(page + 1) * page_size]

        if not total_count:
            total_count = controls.count()
        # serializer =
        serializer = serializers.FileControlSemiFullSerializer(
            controls, many=True, context={'request': request})
        related_petitions = Petition.objects.filter(
            file_controls__file_control__in=controls)\
            .prefetch_related(
                "petition_months",
                "file_controls",
                "break_dates",
                "negative_reasons",
                "negative_reasons__negative_reason",
                "file_controls"
            ).distinct()
        serializer_petitions = PetitionSemiFullSerializer(
            related_petitions, many=True, context={'request': request})
        data = {
            "file_controls": serializer.data,
            "petitions": serializer_petitions.data,
            "total_count": total_count,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path='columns')
    def columns(self, request, **kwargs):
        from inai.models import FileControl
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

            column_serializer = NameColumnEditSerializer(
                column, data=column_item)
            if column_serializer.is_valid():
                print("es válido")
                column = column_serializer.save()
                actual_id_columns.append(column.id)
                actual_id_tranformations = []
                for transf_item in transformations:
                    transformation = Transformation()
                    transf_item["name_column"] = column.id
                    transform_ser = TransformationEditSerializer(
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
        new_serializer = FileControlFullSerializer(
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
            function_name = "massive_explore" \
                if method == "buildExploreDataFile" else "massive_count"
            key_task, task_params = build_task_params(
                file_control, function_name, request, subgroup=status_name)
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
                "file_control": FileControlFullSerializer(
                    file_control).data,
            }
            comprobate_status(key_task, errors=all_errors, new_tasks=all_tasks)
            data["new_task"] = key_task.id
            return Response(data, status=status.HTTP_200_OK)
            # elif method == 'countFile':

        # print("STATUS", status_req)

        return Response({"errors": ["No se encontró el método"]},
                        status=status.HTTP_400_BAD_REQUEST)
