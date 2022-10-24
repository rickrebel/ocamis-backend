from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import (
    FileType, StatusControl, ColumnType, NegativeReason, DateBreak, Anomaly,
    InvalidReason, TransparencyIndex, TransparencyLevel, FileFormat)


class StatusControlAdmin(admin.ModelAdmin):
    list_display = [
        "public_name", "group", "order", "name", "description",
        "color", "icon", "addl_params"]
    list_editable = ["order", "color"]
    list_filter = ["group"]

ocamis_admin_site.register(StatusControl, StatusControlAdmin)


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ["public_name", "name", "group", "is_default", "has_data", "order",
        "addl_params"]
    list_filter = ["has_data", "group"]

ocamis_admin_site.register(FileType, FileTypeAdmin)


class FileFormatAdmin(admin.ModelAdmin):
    list_display = ["short_name", "public_name", "suffixes", "readable"]

ocamis_admin_site.register(FileFormat, FileFormatAdmin)


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


class InvalidReasonAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]

ocamis_admin_site.register(InvalidReason, InvalidReasonAdmin)


class AnomalyAdmin(admin.ModelAdmin):
    list_display = ["public_name", "name", "is_public", "description"]

ocamis_admin_site.register(Anomaly, AnomalyAdmin)


class TransparencyIndexAdmin(admin.ModelAdmin):
    list_display = ["short_name", "public_name", "description"]

ocamis_admin_site.register(TransparencyIndex, TransparencyIndexAdmin)


class TransparencyLevelAdmin(admin.ModelAdmin):
    list_display = [
    "short_name", "public_name", "value",
    "final_level"]

ocamis_admin_site.register(TransparencyLevel, TransparencyLevelAdmin)
