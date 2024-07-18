from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination


from api.mixins import (
    MultiSerializerModelViewSet, MultiSerializerListRetrieveUpdateMix)
from inai.api.serializers import (
    PetitionSemiFullSerializer, PetitionFileControlDeepSerializer,
    FileControlFullSerializer, TransformationEditSerializer,
    NameColumnEditSerializer)
from respond.api.serializers import DataFileSerializer
from inai.models import PetitionFileControl
from respond.models import DataFile, SheetFile
from task.builder import TaskBuilder
from task.helpers import HttpResponseError
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
        filter_name = filter_item["name"]
        if limiters.get(filter_name):
            final_filters[filter_item["field"]] = limiters.get(filter_name)
    if limiters.get("has_notes"):
        final_filters["notes__isnull"] = not limiters.get("has_notes")
    if limiters.get("status_task"):
        final_filters["id__in"] = limiters.get("related_ids", [])
    if limiters.get("agency_type"):
        if limiters.get("agency_type") == 'Hospital Federal':
            final_filters["agency__clues__isnull"] = False
        elif limiters.get("agency_type") == 'Estatal':
            final_filters["agency__clues__isnull"] = True
            final_filters["agency__state__isnull"] = False
        else:
            final_filters["agency__clues__isnull"] = True
            final_filters["agency__state__isnull"] = True
    return final_filters


class FileControlViewSet(MultiSerializerModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.FileControlSerializer
    pagination_class = HeavyResultsSetPagination
    queryset = FileControl.objects.all().prefetch_related(
        "data_group",
        "columns",
        "columns__column_transformations",
        "file_transformations",
        "petition_file_control",
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["show_institution"] = True
        # context["show_institution"] = self.kwargs['customer_id']
        # context["query_params"] = self.request.query_params
        return context

    action_serializers = {
        "list": serializers.FileControlSemiFullSerializer,
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
        )
        if status_register:
            controls = controls.filter(status_register_id=status_register)
        return controls

    def retrieve(self, request, **kwargs):
        from task.models import ClickHistory
        print("ESTOY EN GET")
        file_control = self.get_object()
        ClickHistory.objects.create(
            user=request.user, file_control=file_control)
        serializer = FileControlFullSerializer(
            file_control, context={'request': request})
        data = serializer.data
        data_files = DataFile.objects\
            .filter(petition_file_control__file_control=file_control)
        # data_files = file_control.petition_file_control.data_files.all()
        data["data_files_count"] = data_files.count()
        data["filter_data_files"] = data["data_files_count"]
        sheet_files = SheetFile.objects\
            .filter(data_file__petition_file_control__file_control=file_control)
        data["sheet_files_count"] = sheet_files.count()
        data["data_files"] = []
        return Response(data, status=status.HTTP_200_OK)

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
            return Response({"errors": serializer_ctrl.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        if petition_id:
            new_pet_file_ctrl = PetitionFileControl.objects.create(
                petition_id=petition_id, file_control=file_control)

            new_serializer = PetitionFileControlDeepSerializer(
                new_pet_file_ctrl, context={'request': request})
            return Response(
                new_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"errors": "No se ha podido crear el control de archivo"},
                status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        from data_param.models import CleanFunction
        file_control = self.get_object()
        data = request.data

        serializer_file_control = self.get_serializer_class()(
            file_control, data=data)
        if serializer_file_control.is_valid():
            serializer_file_control.save()
        else:
            return Response({"errors": serializer_file_control.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        transformations = data.pop('transformations', None)
        clean_intermediary = CleanFunction.objects.filter(
            name='horizontal_repeat').first()
        if transformations is not None:
            actual_id_transformations = []
            for transf_item in transformations:
                transformation = Transformation()
                transform_ser = TransformationEditSerializer(
                    transformation, data=transf_item)
                if transform_ser.is_valid():
                    tranform = transform_ser.save()
                    actual_id_transformations.append(tranform.id)
                    if tranform.clean_function_id == clean_intermediary.id:
                        file_control.is_intermediary = True
                        file_control.save()
            Transformation.objects.filter(file_control=file_control) \
                .exclude(id__in=actual_id_transformations).delete()

        new_file_control = FileControl.objects.get(id=file_control.id)
        new_serializer = FileControlFullSerializer(new_file_control)
        return Response(
            new_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

        # return Response(
        #    serializer_file_control.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=["get"], detail=True, url_path='data_files')
    def data_files(self, request, **kwargs):
        import json
        from django.db.models import Q
        file_control = self.get_object()
        data_files = DataFile.objects\
            .filter(petition_file_control__file_control=file_control) \
            .order_by("-id")\
            .prefetch_related(
                "sheet_files", "petition_file_control", "sheet_files__laps")
        limiters = request.query_params.get("limiters", None)
        limiters = json.loads(limiters)
        available_filters = [
            {"name": "pfc", "field": "petition_file_control_id"},
            {"name": "stage", "field": "stage_id"},
            {"name": "status", "field": "status_id"},
        ]
        if limiters:
            final_filters = {}
            for filter_item in available_filters:
                filter_value = limiters.get(filter_item["name"])
                if filter_value:
                    final_filters[filter_item["field"]] = filter_value
            if final_filters:
                data_files = data_files.filter(**final_filters)
        txt = limiters.get("text", None)
        if txt:
            data_files = data_files.filter(
                Q(file__icontains=txt) |
                Q(petition_file_control__petition__folio_petition=txt))
        is_duplicated = limiters.get("is_duplicated", None)
        if is_duplicated is not None:
            data_files = data_files.filter(is_duplicated=is_duplicated)
        sts = limiters.get("status_built", [])
        final_files = None
        for status_built in sts:
            [status_id, stage_id] = status_built.split("-")
            current_files = data_files\
                .filter(status_id=status_id, stage_id=stage_id)
            final_files = current_files if not final_files \
                else final_files | current_files
        if final_files:
            final_files = final_files.distinct().order_by("-id")
        else:
            final_files = data_files
        # print("STS_PROCESS", sts_process)
        total_count = final_files.count()
        page_size = limiters.get("page_size", 30)
        page = limiters.get("page", 1) - 1
        final_files2 = final_files[page * page_size:(page + 1) * page_size]
        serializer_files = DataFileSerializer(final_files2, many=True).data
        data = {
            "total_count": total_count,
            "data_files": serializer_files,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True, url_path='sheet_files')
    def sheet_files(self, request, **kwargs):
        import json
        from respond.api.serializers import SheetFileTableSerializer
        from django.db.models import Q
        file_control = self.get_object()
        limiters = request.query_params.get("limiters", None)
        limiters = json.loads(limiters)

        # print("STS_PROCESS", sts_process)
        page_size = limiters.get("page_size", 30)
        page = limiters.get("page", 1) - 1
        filters = {"data_file__petition_file_control__file_control": file_control}
        if behavior := limiters.get("behavior", None):
            filters["behavior_id"] = behavior
        order = limiters.get("order", "-id")
        sheet_files = SheetFile.objects\
            .filter(**filters)\
            .order_by(order)\
            .prefetch_related("laps")
        total_count = sheet_files.count()

        final_sheets = sheet_files[page * page_size:(page + 1) * page_size]
        serializer_files = SheetFileTableSerializer(final_sheets, many=True).data
        data = {
            "total_count": total_count,
            "sheet_files": serializer_files,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True, url_path='lap_sheets')
    def lap_sheets(self, request, **kwargs):
        import json
        # from django.db.models import Q
        from respond.api.serializers import LapSheetTableSerializer
        from respond.models import LapSheet
        file_control = self.get_object()
        limiters = request.query_params.get("limiters", None)
        limiters = json.loads(limiters)

        # print("STS_PROCESS", sts_process)
        page_size = limiters.get("page_size", 30)
        page = limiters.get("page", 1) - 1
        filters = {
            "sheet_file__data_file__petition_file_control__file_control": file_control,
            "lap__gte": 0,
            "sheet_file__matched": True,
        }
        if behavior := limiters.get("behavior", None):
            filters["sheet_file__behavior_id"] = behavior
        if search_text := limiters.get("search", None):
            filters["sheet_file__file__icontains"] = search_text
        order = limiters.get("order", "-sheet_file_id")
        lap_sheets = LapSheet.objects\
            .filter(**filters)\
            .order_by(order)\
            .select_related("sheet_file", "sheet_file__data_file",
                            "sheet_file__data_file__petition_file_control")\
            .prefetch_related("table_files")

        total_count = lap_sheets.count()

        final_laps = lap_sheets[page * page_size:(page + 1) * page_size]
        serializer_laps = LapSheetTableSerializer(final_laps, many=True).data
        data = {
            "total_count": total_count,
            "lap_sheets": serializer_laps,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path='filter')
    def filter(self, request, **kwargs):
        from data_param.models import FileControl, CleanFunction
        from inai.models import Petition
        from inai.api.views import get_petition_related_months
        import json
        limiters = request.query_params.get("limiters", "{}")
        limiters = json.loads(limiters)
        total_count = 0
        available_filters = [
            {"name": "status_register", "field": "status_register_id"},
            {"name": "data_group", "field": "data_group_id"},
            {"name": "file_format", "field": "file_format_id"},
            # {"name": "final_field", "field": "columns__final_field_id"},
        ]
        # if limiters:
        all_filters = build_common_filters(limiters, available_filters)
        final_field = limiters.get("final_field", None)
        if final_field is not None:
            if final_field == 0:
                all_filters["columns__final_field__isnull"] = True
            else:
                all_filters["columns__final_field_id"] = limiters["final_field"]
        stage = limiters.get("stage", None)
        if stage is not None:
            all_filters["petition_file_control__data_files__stage_id"] = stage
        is_duplicated = limiters.get("is_duplicated", None)
        print("IS_DUPLICATED", is_duplicated)
        if is_duplicated is not None:
            str_filter = "petition_file_control__data_files__is_duplicated"
            all_filters[str_filter] = is_duplicated
        transformation = limiters.get("transformation", None)
        if transformation is not None:
            clean_function = CleanFunction.objects.get(id=transformation)
            if clean_function.for_all_data:
                text = "file_transformations__clean_function_id"
            else:
                text = "columns__column_transformations__clean_function_id"
            all_filters[text] = transformation
        status_id = limiters.get("status", None)
        if status_id is not None:
            all_filters["petition_file_control__data_files__status_id"] = status_id

        order = ["agency__acronym", "name", "data_group"]
        controls = FileControl.objects.all().prefetch_related(
            "data_group",
            "columns",
            "columns__column_transformations",
            "columns__column_transformations__clean_function",
            "file_transformations",
            "file_transformations__clean_function",
            "agency",
        ).order_by(*order)
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
                # "petition_months",
                "month_records",
                "file_controls",
                "break_dates",
                "negative_reasons",
                "negative_reasons__negative_reason",
                "file_controls"
            ).distinct()
        serializer_petitions = PetitionSemiFullSerializer(
            related_petitions, many=True, context={'request': request})
        related_month_records = get_petition_related_months(serializer_petitions)
        data = {
            "file_controls": serializer.data,
            "petitions": serializer_petitions.data,
            "total_count": total_count,
            "related_month_records": related_month_records,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path='columns')
    def columns(self, request, **kwargs):
        from data_param.models import FileControl
        columns_items = request.data.get("columns")
        file_control = self.get_object()
        # limiters = json.loads(limiters)

        actual_id_columns = []
        for (order, column_item) in enumerate(columns_items, start=1):
            column_id = column_item.get("id", False)
            transformations = column_item.pop('transformations', [])
            # print("TRANSFORMATIONS", transformations)
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
                # print("es válido")
                column = column_serializer.save()
                actual_id_columns.append(column.id)
                actual_id_transformations = []
                for transf_item in transformations:
                    transformation = Transformation()
                    transf_item["name_column"] = column.id
                    transform_ser = TransformationEditSerializer(
                        transformation, data=transf_item)
                    if transform_ser.is_valid():
                        print("transf válido")
                        tranform = transform_ser.save()
                        actual_id_transformations.append(tranform.id)
                        print("transf_id", tranform.id)
                    else:
                        print("NO ES VALIDO", transform_ser.errors)
                Transformation.objects.filter(name_column=column) \
                    .exclude(id__in=actual_id_transformations).delete()
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

    @action(methods=["put"], detail=True, url_path='massive_change_stage')
    def massive_change_stage(self, request, **kwargs):
        from classify_task.models import Stage
        from respond.data_file_mixins.explore_mix import ExploreRealMix

        file_control = self.get_object()
        stage_init = request.data.get("stage_init")
        status_init = request.data.get("status_init")
        batch_size = request.data.get("batch_size", 30)
        batch_size = int(batch_size)

        stage_final = request.data.get("stage_final")
        target_stage = Stage.objects.get(name=stage_final)
        target_name = target_stage.main_function.name

        all_data_files = DataFile.objects.filter(
            petition_file_control__file_control=file_control,
            status_id=status_init, stage_id=stage_init)[:batch_size*2]
        curr_kwargs = {}
        function_after = None
        if target_stage.function_after:
            function_after = target_stage.function_after.name
            curr_kwargs = {"function_after": function_after}
        subgroup = f"{stage_init}|{status_init}"

        base_task = TaskBuilder(
            function_name=target_name, is_massive=True,
            models=[file_control], request=request, subgroup=subgroup)
        final_count = 0
        for data_file in all_data_files:
            if not data_file.can_repeat:
                continue
            if final_count >= batch_size:
                break
            final_count += 1
            df_task = TaskBuilder(
                function_name=target_stage.main_function.name,
                models=[data_file], request=request, is_massive=True,
                subgroup=subgroup, parent_class=base_task)

            for re_stage in target_stage.re_process_stages.all():
                current_function = re_stage.main_function.name
                on_target = re_stage.name == target_name

                re_task = TaskBuilder(
                    function_name=current_function, parent_class=df_task,
                    models=[data_file], request=request,
                    function_after=function_after)
                explore = ExploreRealMix(data_file, base_task=re_task)
                try:
                    # possible_functions: get_sample_data, verify_coincidences,
                    # prepare_transform, transform_data
                    getattr(explore, current_function)(**curr_kwargs)
                except HttpResponseError as e:
                    if e.errors:
                        data_file.save_errors(e.errors, f"{re_stage.name}|with_errors")
                    break
                if on_target:
                    data_file = data_file.finished_stage(f"{target_name}|finished")
                    df_task.comprobate_status(want_http_response=False)
        base_task.comprobate_status(want_http_response=False)
        data = {
            "errors": base_task.errors,
            "file_control": FileControlFullSerializer(file_control).data,
            "new_tasks": base_task.main_task.id
        }
        return Response(data, status=status.HTTP_200_OK)


class NameColumnViewSet(MultiSerializerListRetrieveUpdateMix):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.NameColumnSerializer
    queryset = NameColumn.objects.all()

    action_serializers = {
        "patch": serializers.NameColumnSerializer,
    }
