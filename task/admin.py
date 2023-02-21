from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import (
    StatusTask, AsyncTask, TaskFunction)


class StatusTaskAdmin(admin.ModelAdmin):
    list_display = [
        "name", "public_name", "order", "description", "color", "icon",
        "is_completed"]
    list_editable = ["order", "color", "is_completed"]


ocamis_admin_site.register(StatusTask, StatusTaskAdmin)


class AsyncTaskAdmin(admin.ModelAdmin):
    list_display = [
        "request_id",
        # "function_name",
        "task_function",
        "status_task",
        "is_current",
        "date_start",
        "date_end",
    ]
    raw_id_fields = ["petition", "file_control", "data_file", "process_file"]


ocamis_admin_site.register(AsyncTask, AsyncTaskAdmin)


class TaskFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model_name",
        "public_name",
    ]


ocamis_admin_site.register(TaskFunction, TaskFunctionAdmin)
