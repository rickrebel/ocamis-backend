from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import (
    FileType, StatusControl, ColumnType, NegativeReason, DateBreak)


class StatusControlAdmin(admin.ModelAdmin):
    list_display = [
        "group", "name", "public_name", "description", "order",
        "addl_params", "color"]
    list_filter = ["group"]

ocamis_admin_site.register(StatusControl, StatusControlAdmin)


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "is_default", "has_data", "order",
        "addl_params"]
    list_filter = ["has_data", "group"]

ocamis_admin_site.register(FileType, FileTypeAdmin)


class ColumnTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name", "description"]

ocamis_admin_site.register(ColumnType, ColumnTypeAdmin)


class DateBreakAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name", "group", "order"]
    list_filter = ["group"]

ocamis_admin_site.register(DateBreak, DateBreakAdmin)


class NegativeReasonAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]

ocamis_admin_site.register(NegativeReason, NegativeReasonAdmin)
