from django.contrib import admin

from .models import FileType, StatusControl, ColumnType, NegativeReason


class StatusControlAdmin(admin.ModelAdmin):
    list_display = ["group", "name", "public_name", "addl_params"]
    list_filter = ["group"]

admin.site.register(StatusControl, StatusControlAdmin)


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "has_data", "order"]
    list_filter = ["has_data"]

admin.site.register(FileType, FileTypeAdmin)


class ColumnTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name", "description"]

admin.site.register(ColumnType, ColumnTypeAdmin)


class NegativeReasonAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]

admin.site.register(NegativeReason, NegativeReasonAdmin)
