# from django.contrib import admin
# from inai.admin import ocamis_admin_site
# from django.utils.html import format_html
#
# from .models import (
#     FileType, StatusControl, ColumnType, NegativeReason, DateBreak, Anomaly,
#     InvalidReason, TransparencyIndex, TransparencyLevel, FileFormat)
# from task.models import StatusTask
#
#
# class StatusControlAdmin(admin.ModelAdmin):
#     list_display = [
#          "name", "public_name", "group", "order","description",
#         "color", "icon", "addl_params"]
#     list_editable = ["order", "color"]
#     list_filter = ["group"]
#
# ocamis_admin_site.register(StatusControl, StatusControlAdmin)
#
#
# class FileTypeAdmin(admin.ModelAdmin):
#     list_display = ["public_name", "name", "group", "is_default", "has_data", "order",
#         "addl_params"]
#     list_filter = ["has_data", "group"]
#
# ocamis_admin_site.register(FileType, FileTypeAdmin)
#
#
# class FileFormatAdmin(admin.ModelAdmin):
#     list_display = ["short_name", "public_name", "suffixes", "readable"]
#
# ocamis_admin_site.register(FileFormat, FileFormatAdmin)
#
#
# class ColumnTypeAdmin(admin.ModelAdmin):
#     list_display = ["name", "public_name", "description"]
#
# ocamis_admin_site.register(ColumnType, ColumnTypeAdmin)
#
#
# class DateBreakAdmin(admin.ModelAdmin):
#     list_display = ["name", "public_name", "group", "order"]
#     list_filter = ["group"]
#
# ocamis_admin_site.register(DateBreak, DateBreakAdmin)
#
#
# class NegativeReasonAdmin(admin.ModelAdmin):
#     list_display = ["name", "description"]
#
# ocamis_admin_site.register(NegativeReason, NegativeReasonAdmin)
#
#
# class InvalidReasonAdmin(admin.ModelAdmin):
#     list_display = ["name", "description"]
#
# ocamis_admin_site.register(InvalidReason, InvalidReasonAdmin)
#
#
# class AnomalyAdmin(admin.ModelAdmin):
#     list_display = ["public_name", "name", "is_public", "description"]
#
# ocamis_admin_site.register(Anomaly, AnomalyAdmin)
#
#
# class TransparencyLevelInline(admin.StackedInline):
#     model = TransparencyLevel
#     extra = 0
#
#
# class TransparencyIndexAdmin(admin.ModelAdmin):
#     list_display = ["short_name", "public_name", "description"]
#     inlines = [ TransparencyLevelInline ]
#
# ocamis_admin_site.register(TransparencyIndex, TransparencyIndexAdmin)
#
#
# class TransparencyLevelAdmin(admin.ModelAdmin):
#     list_display = [
#         "short_name", "public_name", "display_index", "display_final", "value",
#         "order_viz", "value_ctrls", "value_pets", "is_default"]
#     list_editable = [
#         "value", "order_viz", "value_ctrls", "value_pets", "is_default"]
#     list_filter = ["transparency_index"]
#
#     def display_index(self, obj):
#         names = [
#             obj.transparency_index.public_name,
#             f"({obj.transparency_index.short_name})"]
#         return format_html("<br>".join(names))
#     display_index.short_description = "Indicador"
#
#     def display_final(self, obj):
#         return format_html(obj.final_level.public_name) if obj.final_level else ""
#     display_final.short_description = "Concentrado destino"
#
#
# ocamis_admin_site.register(TransparencyLevel, TransparencyLevelAdmin)
#
#
