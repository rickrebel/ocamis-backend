from django.contrib import admin
from inai.admin import ocamis_admin_site
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    AsyncTask, CutOff, Step, ClickHistory, OfflineTask)
from rds.models import Platform
from classify_task.models import StatusTask, TaskFunction, Stage, UserProfile


class NullFilterTask(SimpleListFilter):
    title = "Con clicks"

    parameter_name = 'has_field'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Es derivado', ),
            ('0', 'Es directo', ),
        )

    def queryset(self, request, queryset):
        kwargs = {'parent_task__isnull': True}
        # kwargs = {'%s' % self.parameter_name: None}
        if self.value() == '0':
            return queryset.filter(**kwargs)
        if self.value() == '1':
            return queryset.exclude(**kwargs)
        return queryset


class AsyncTaskInline(admin.StackedInline):
    raw_id_fields = [
        "petition", "file_control", "data_file", "reply_file", "sheet_file",
        "parent_task", "user", "week_record", "provider", "month_record"]
    model = AsyncTask
    classes = ["collapse"]
    show_change_link = True
    extra = 0


class AsyncTaskAdmin(admin.ModelAdmin):
    list_display = [
        "request_short",
        "display_function",
        "display_status",
        "date",
        "display_other_dates",
        "is_current",
    ]
    raw_id_fields = [
        "petition", "file_control", "data_file", "reply_file", "sheet_file",
        "parent_task", "user", "week_record", "provider", "month_record",
        "cluster", "operation", "mat_view"]
    list_filter = [
        NullFilterTask,
        "status_task", "task_function__is_queueable",
        "status_task__is_completed",
        "task_function", "user", "status_task__macro_status",
        "function_after", "parent_task__task_function",
        "is_current", "is_massive"]
    search_fields = ["data_file_id", "request_id", "task_function__name"]
    # inlines = [AsyncTaskInline]
    # return format_html(obj.final_level.public_name) if obj.final_level else ""

    @staticmethod
    def request_short(obj):
        if obj.request_id:
            return obj.request_id[-12:]
        return obj.id

    @staticmethod
    def date(obj):
        from datetime import datetime
        from django.utils.timezone import get_current_timezone, make_aware
        if not obj.date_start:
            return ""
        tz = get_current_timezone()
        date = make_aware(datetime.fromtimestamp(obj.date_start.timestamp()), tz)
        date_string = date.strftime("%d-%b <br> <b>%H:%M:%S</b>")
        return format_html(date_string)

    def display_function(self, obj):
        if obj.task_function:
            all_texts = [
                f"<b>{obj.task_function.name}</b>",
                f"({obj.task_function.model_name})",
            ]
        else:
            all_texts = ["???", "???"]
        return format_html("<br>".join(all_texts))
    display_function.short_description = "Función"

    def display_status(self, obj):
        import json
        # ▶️
        macro_status = obj.status_task.macro_status
        # icon = "🛑⛔🚫⭕❌❗‼️⚠️✅🟣🔴🟠🟡⚪"
        if macro_status == "finished":
            icon = "🟢"
        elif macro_status == "created":
            icon = "🟣"
        elif macro_status == "pending":
            icon = "🟡"
        elif macro_status == "with_errors":
            icon = "🛑"
        else:
            icon = "❔"
        div = f"""
            <div title='{json.dumps(obj.errors)[:8000]}'>
            {icon} {obj.status_task.public_name}
            </div>
        """
        div_simple = f"""
            <div>
            {icon} {obj.status_task.public_name}
            </div>
        """
        try:
            return format_html(div)
        except Exception as e:
            print("e 2", e)
            return format_html(div_simple)
    display_status.short_description = "Status"

    def display_other_dates(self, obj):

        def calc_time_ago(date1, date2):
            try:
                seconds = (date1 - date2).total_seconds()
                abs_seconds = abs(seconds)
                # if abs_seconds < 3:
                #     return None
                if abs_seconds < 5:
                    return f"<span style='color: grey;'>" \
                           f"{round(abs_seconds, 2)} secs </span>"
                if abs_seconds < 60:
                    return f"{round(abs_seconds, 2)} secs"
                minutes = round(abs(seconds) / 60, 2)
                if minutes < 60:
                    return f"<b>{minutes} mins</b>"
                hours = round(abs(minutes) / 60, 2)
                return f"<b>{hours} hrs</b>"
            except TypeError as e:
                print("e 3", e)
                return f"NADA, {e}"
        all_texts = []
        fields2 = [
            {"name": "date_sent", "display": "sent"},
            {"name": "date_arrive", "display": "AWS"},
            {"name": "date_end", "display": "end"}
        ]
        last_date = getattr(obj, "date_start")
        for field in fields2:
            value = getattr(obj, field["name"])
            if value:
                time_ago = calc_time_ago(value, last_date)
                if time_ago:
                    all_texts.append(f"{time_ago} -{field['display']}")
                    last_date = value
        # if not obj.date_end and not obj.date_arrive:
        #     return ""
        # end = getattr(obj, "date_end")
        # arrive = getattr(obj, "date_arrive")
        # all_texts = []
        # last_date = getattr(obj, "date_start")
        # if arrive:
        #     time_ago = calc_time_ago(arrive, obj.date_start)
        #     all_texts.append(f"+{time_ago} (AWS)")
        #     last_date = arrive
        # if end:
        #     time_ago = calc_time_ago(end, last_date)
        #     all_texts.append(f"+{time_ago} (end)")

        return format_html("<br>".join(all_texts))
    display_other_dates.short_description = "end"


class StatusTaskAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "public_name",
        "order",
        "color",
        "icon",
        "is_completed",
        "macro_status",
    ]
    list_editable = ["order", "color", "is_completed"]


class TaskFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_active",
        "public_name",
        "is_from_aws",
        "is_queueable",
        "ebs_percent",
        "model_name",
        # "queue_size",
        # "group_queue",
    ]
    # list_editable = ["public_name", "is_active"]
    list_filter = ["is_active", "is_queueable", "is_from_aws", "model_name"]


class StageAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        # "name",
        # "description",
        # "public_name",
        "stage_group",
        "order",
        # "next_stage",
        "main_function",
        "finished_function",
        "icon",
        # "retry_function",
    ]
    list_editable = ["order"]


class PlatformAdmin(admin.ModelAdmin):
    list_display = [
        "version",
        "has_constrains",
    ]
    list_editable = ["version", "has_constrains"]


class ProfileInLine(admin.StackedInline):
    model = UserProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields':
                              ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields':
            ('is_active', 'is_staff', 'is_superuser', "groups")}),
    )
    inlines = [ProfileInLine]
    list_display = ["username", "email", "first_name", "last_name",
                    "is_active", "is_superuser"]


class StepInline(admin.TabularInline):
    model = Step
    extra = 0


class CutOffAdmin(admin.ModelAdmin):
    list_display = [
        "provider",
        "last_month_record",
    ]
    raw_id_fields = ["provider", "last_month_record"]
    inlines = [StepInline]


class ClickHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "petition", "file_control", "month_record"]
    raw_id_fields = ["user", "petition", "file_control", "month_record"]
    list_filter = ["user"]


class OfflineTaskAdmin(admin.ModelAdmin):
    list_display = [
        "activity_type",
        "name",
        "date_start",
        "date_end",
    ]


admin.site.unregister(User)
# admin.site.unregister(Token)
ocamis_admin_site.register(User, CustomUserAdmin)

ocamis_admin_site.register(AsyncTask, AsyncTaskAdmin)
ocamis_admin_site.register(StatusTask, StatusTaskAdmin)
ocamis_admin_site.register(TaskFunction, TaskFunctionAdmin)
ocamis_admin_site.register(Stage, StageAdmin)
# ocamis_admin_site.register(Platform, PlatformAdmin)
ocamis_admin_site.register(Platform)
ocamis_admin_site.register(CutOff, CutOffAdmin)
ocamis_admin_site.register(ClickHistory, ClickHistoryAdmin)
ocamis_admin_site.register(OfflineTask, OfflineTaskAdmin)
