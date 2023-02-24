from django.contrib import admin
from inai.admin import ocamis_admin_site
from django.utils.html import format_html

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
        # "request_id",
        "request_short",
        # "function_name",
        "task_function",
        "status_task",
        "is_current",
        "display_other_dates",
        # "date_start",
        "start_simple",
        # "date_end",
    ]
    raw_id_fields = ["petition", "file_control", "data_file", "process_file"]
    list_filter = ["status_task", "task_function", "is_current"]
    # return format_html(obj.final_level.public_name) if obj.final_level else ""

    @staticmethod
    def request_short(obj):
        if obj.request_id:
            return obj.request_id[-12:]
        return obj.id

    @staticmethod
    def start_simple(obj):
        from datetime import datetime
        from django.utils.timezone import make_aware
        from django.utils.timezone import get_current_timezone
        tz = get_current_timezone()
        date = make_aware(datetime.fromtimestamp(obj.date_start.timestamp()), tz)
        date_string = date.strftime("%d-%m-%Y <br> <b>%H:%M</b>")
        return format_html(date_string)

    def display_other_dates(self, obj):
        from datetime import datetime

        def calc_time_ago(date1, date2):
            try:
                seconds = (date1 - date2).total_seconds()
                if abs(seconds) < 60:
                    return f"{round(seconds, 2)} sec"
                minutes = round(seconds / 60, 1)
                if abs(minutes) < 60:
                    return f"{minutes} min"
                hours = round(minutes / 60, 2)
                return f"{hours} hrs"
            except TypeError as e:
                print("e", e)
                return "NADAAA"
        if not obj.date_end and not obj.date_arrive:
            return ""
        end = getattr(obj, "date_end")
        arrive = getattr(obj, "date_arrive")
        all_texts = []
        last_date = getattr(obj, "date_start")
        if arrive:
            time_ago = calc_time_ago(arrive, obj.date_start)
            all_texts.append(f"+{time_ago} (AWS)")
            last_date = arrive
        if end:
            time_ago = calc_time_ago(end, last_date)
            all_texts.append(f"+{time_ago} (end)")

        return format_html("<br>".join(all_texts))
    display_other_dates.short_description = "end"


ocamis_admin_site.register(AsyncTask, AsyncTaskAdmin)


class TaskFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model_name",
        "public_name",
    ]


ocamis_admin_site.register(TaskFunction, TaskFunctionAdmin)
