from rest_framework import permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from api.mixins import (
    MultiSerializerListRetrieveMix as ListRetrieveView,
    MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateView,
    CreateMix)


from task.api import serializers
from task.models import AsyncTask, CutOff, Step

prefetch_async = [
    "data_file",
    "sheet_file",
    "data_file__petition_file_control",
    "reply_file",
    "file_control",
    "file_control__petition_file_control",
]


class AsyncTaskViewSet(ListRetrieveView):
    queryset = AsyncTask.objects.all()
    serializer_class = serializers.AsyncTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.AsyncTaskSerializer,
        "retrieve": serializers.AsyncTaskSerializer,
    }

    def get_queryset(self):
        return AsyncTask.objects.all().prefetch_related(
            "data_file",
            "data_file__petition_file_control",
            "reply_file",
            "file_control",
            "file_control__petition_file_control",
        )

    @action(methods=["get"], detail=False, url_path='restart_queue')
    def restart_queue(self, request, **kwargs):
        from task.views import debug_queue
        debug_queue()
        return Response(
            {"message": "Cola reiniciada"}, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path='last_hours')
    def last_hours(self, request, **kwargs):
        from datetime import datetime, timedelta
        from django.contrib.auth.models import User
        from auth.api.serializers import UserProfileSerializer
        total_hours = request.query_params.get("hours", 3)
        now = datetime.now()
        last_hours = now - timedelta(hours=int(total_hours))
        task_by_start = AsyncTask.objects\
            .filter(date_start__gte=last_hours)\
            .prefetch_related(*prefetch_async)
        task_by_end = AsyncTask.objects\
            .filter(date_end__gte=last_hours)\
            .prefetch_related(*prefetch_async)
        all_tasks = task_by_start | task_by_end
        staff_users = User.objects.filter(
            is_staff=True, is_active=True, profile__isnull=False)
        staff_data = UserProfileSerializer(staff_users, many=True).data
        data = {
            "tasks": serializers.AsyncTaskSerializer(all_tasks, many=True).data,
            "staff_users": staff_data,
            "last_request": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path='news')
    def news(self, request, **kwargs):
        from datetime import datetime, timedelta

        now = datetime.now()
        last_request = request.query_params.get("last_request")
        #format_string = "%a %b %d %Y %H:%M:%S GMT%z (%Z)"
        #last_request = datetime.strptime(last_request, format_string)

        # convert unix timestamp to datetime
        try:
            # epoch_time = (int(last_request)/1000) + (3600 * 6)
            last_request = datetime.strptime(last_request, "%Y-%m-%d %H:%M:%S")
            last_request -= timedelta(seconds=120)
            # last_request = datetime.fromtimestamp(epoch_time)
        except Exception as e:
            print("ERROR: ", e)
            last_request = now - timedelta(hours=3)

        task_by_start = AsyncTask.objects\
            .filter(date_start__gte=last_request)\
            .prefetch_related(*prefetch_async)
        task_by_end = AsyncTask.objects\
            .filter(date_end__gte=last_request)\
            .prefetch_related(*prefetch_async)
        all_tasks = task_by_start | task_by_end
        data = {
            "new_tasks": serializers.AsyncTaskSerializer(all_tasks, many=True).data,
            "last_request": now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_request_sent": last_request.strftime("%Y-%m-%d %H:%M:%S"),
            "last_task": AsyncTask.objects.first().date_start.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return Response(data, status=status.HTTP_200_OK)


class CutOffViewSet(ListRetrieveView):
    queryset = CutOff.objects.all().prefetch_related(
        "steps", "last_entity_month")
    serializer_class = serializers.CutOffSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.CutOffSerializer,
        "retrieve": serializers.CutOffSerializer,
    }

    def get_queryset(self):
        return CutOff.objects.all().prefetch_related(
            "steps", "last_entity_month")

    def create(self, request, *args, **kwargs):
        from inai.models import EntityMonth
        from classify_task.models import Stage
        from category.models import StatusControl
        year = request.data.get("year")
        month = request.data.get("month")
        year_month = f"{year}-{str(month).zfill(2)}"
        entity_id = request.data.get("entity_id")
        entity_month = EntityMonth.objects.filter(
            year_month=year_month, entity_id=entity_id).first()
        cut_off = CutOff.objects.create(
            last_entity_month=entity_month, entity_id=entity_id)
        entity_stages = Stage.objects\
            .filter(stage_group__contains="provider-")\
            .order_by("-order")
        initial_status = StatusControl.objects.get(
            name="initial", group="register")
        for stage in entity_stages:
            Step.objects.get_or_create(
                cut_off=cut_off, stage=stage, status_opera=initial_status)
        new_cut_off = CutOff.objects.get(id=cut_off.id)
        serializer_cut_off = serializers.CutOffSerializer(new_cut_off).data
        return Response(serializer_cut_off, status=status.HTTP_201_CREATED)


class StepViewSet(ListRetrieveUpdateView):
    queryset = Step.objects.all()
    serializer_class = serializers.StepSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.StepSerializer,
        "retrieve": serializers.StepSerializer,
    }

    def get_queryset(self):
        return Step.objects.all()

    def update(self, request, *args, **kwargs):
        from django.utils import timezone
        step = self.get_object()
        data_step = request.data
        print("data_step", data_step)
        data_step["user"] = request.user.id
        data_step["last_update"] = timezone.now()
        print("step", step)
        print("step.user_id", step.user_id)
        serializer_step = self.get_serializer_class()(
            step, data=data_step)
        if serializer_step.is_valid():
            serializer_step.save()
            return Response(serializer_step.data)
        else:
            return Response(
                serializer_step.errors, status=status.HTTP_400_BAD_REQUEST)


class OfflineTaskViewSet(CreateMix):
    queryset = AsyncTask.objects.filter(parent_task__isnull=True)
    serializer_class = serializers.OfflineTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        data["user_added"] = request.user.id
        serializer = serializers.OfflineTaskSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivityView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from task.api.activity import BuildSpendGroups
        from django.utils import timezone
        from datetime import timedelta
        from django.contrib.auth.models import User

        days_ago = request.query_params.get("days_ago", 60)
        user_id = request.query_params.get("user_id", None)
        worker_user = request.user

        if user_id and worker_user.profile.is_manager:
            worker_user = User.objects.get(id=user_id)
        now = timezone.now()
        last_days = now - timedelta(days=int(days_ago))
        tasks = worker_user.async_tasks\
            .filter(date_start__gte=last_days, parent_task__isnull=True)\
            .prefetch_related("task_function")
        tasks_data = serializers.AsyncTaskActivitySerializer(
            tasks, many=True).data
        clicks = worker_user.clicks.filter(date__gte=last_days)
        clicks_data = serializers.ClickHistoryActivitySerializer(
            clicks, many=True).data
        offline = worker_user.offline_tasks.filter(date_start__gte=last_days)
        offline_data = serializers.OfflineTaskActivitySerializer(
            offline, many=True).data
        activities = tasks_data + clicks_data + offline_data
        activities.sort(key=lambda x: x["real_start"], reverse=False)
        all_activities, spend_groups = BuildSpendGroups(activities).build_spend_groups()
        data = {
            "activities": activities,
            "spend_groups": spend_groups,
        }
        return Response(data, status=status.HTTP_200_OK)
