from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.mixins import (
    MultiSerializerListRetrieveMix as ListRetrieveView)

from task.api import serializers
from task.models import AsyncTask


class AsyncTaskViewSet(ListRetrieveView):
    queryset = AsyncTask.objects.all()
    serializer_class = serializers.AsyncTaskFullSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.AsyncTaskFullSerializer,
        "retrieve": serializers.AsyncTaskFullSerializer,
    }

    def get_queryset(self):
        return AsyncTask.objects.all().prefetch_related(
            "data_file",
            "data_file__petition_file_control",
            "reply_file",
            "file_control",
            "file_control__petition_file_control",
        )

    @action(methods=["get"], detail=False, url_path='last_hours')
    def last_hours(self, request, **kwargs):
        from datetime import datetime, timedelta
        from django.contrib.auth.models import User
        from auth.api.serializers import UserDataSerializer
        total_hours = request.query_params.get("hours", 3)
        now = datetime.now()
        last_hours = now - timedelta(hours=int(total_hours))
        task_by_start = AsyncTask.objects\
            .filter(date_start__gte=last_hours)\
            .prefetch_related(
                "data_file",
                "data_file__petition_file_control",
                "reply_file",
                "file_control",
                "file_control__petition_file_control",
            )
        all_tasks = task_by_start
        staff_users = User.objects.filter(is_staff=True)
        staff_data = UserDataSerializer(staff_users, many=True).data
        data = {
            "tasks": serializers.AsyncTaskFullSerializer(all_tasks, many=True).data,
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
            .prefetch_related(
                "data_file",
                "data_file__petition_file_control",
                "reply_file",
                "file_control",
                "file_control__petition_file_control",
            )
        all_tasks = task_by_start
        data = {
            "new_tasks": serializers.AsyncTaskFullSerializer(all_tasks, many=True).data,
            "last_request": now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_request_sent": last_request.strftime("%Y-%m-%d %H:%M:%S"),
            "last_task": AsyncTask.objects.first().date_start.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return Response(data, status=status.HTTP_200_OK)
