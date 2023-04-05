from django.contrib import admin
from inai.admin import ocamis_admin_site
from inai.models import PetitionFileControl

from .models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction,
    ParameterGroup, NameColumn, FileControl, Transformation, DictionaryFile)


class CleanFunctionInLine(admin.StackedInline):
    model = CleanFunction
    extra = 0
    show_change_link = True


class FinalFieldAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "parameter_group",
        "collection",
        "verbose_name",
        "data_type",
        "is_common",
        "is_unique",
        "in_data_base",
        "verified",
        "need_for_viz",
    ]
    list_filter = ["parameter_group", "collection", "verified", "data_type"]
    inlines = [CleanFunctionInLine]
    list_editable = [
        "verbose_name",
        "in_data_base",
        "need_for_viz",
        "is_unique",
        "is_common",
    ]
    ordering = [
        "parameter_group", "collection", "verbose_name"]
    search_fields = [
        "name", "collection__name", "collection__model_name",
        "verbose_name", "parameter_group__name"]


ocamis_admin_site.register(FinalField, FinalFieldAdmin)


class FinalFieldInLine(admin.StackedInline):
    model = FinalField
    extra = 0
    show_change_link = True
    fieldsets = (
        (None, {
            "fields": (
                "collection", "parameter_group",
                "name", "verbose_name", "data_type",
                "regex_format", "is_unique", "in_data_base", "verified",
                "included", "match_use")
        }),
        ("Más configuraciones:", {
            "classes": ("collapse",),
            "fields": (
                "is_required", "is_common", "dashboard_hide",
                "variations", "addl_params")
        }),
        )


class CollectionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model_name",
        "data_group",
        "description",
    ]
    inlines = [
        FinalFieldInLine,
    ]

ocamis_admin_site.register(Collection, CollectionAdmin)


class ParameterGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "data_group",
        "description",
    ]
    inlines = [
        FinalFieldInLine,
    ]


ocamis_admin_site.register(ParameterGroup, ParameterGroupAdmin)


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0


class DataGroupAdmin(admin.ModelAdmin):
    list_display = [
        "public_name",
        "name",
        "is_default",
        "order",
        "color",
    ]
    list_editable = ["color", "order"]
    inlines = [ CollectionInline ]


ocamis_admin_site.register(DataGroup, DataGroupAdmin)


class DataTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "public_name",
        "description",
        "is_common",
        "order",
    ]
    list_editable = ["public_name", "description", "is_common", "order"]


ocamis_admin_site.register(DataType, DataTypeAdmin)


class CleanFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "public_name", "for_all_data", 
        "description", "priority", "addl_params", "column_type"]
    list_editable = ["public_name", "priority"]
    ordering = ["for_all_data", "priority", "public_name"]


ocamis_admin_site.register(CleanFunction, CleanFunctionAdmin)


class PetitionFileControlInline(admin.TabularInline):
    model = PetitionFileControl
    raw_id_fields = ["petition", "file_control"]
    extra = 0


class NameColumnInline(admin.StackedInline):
    model = NameColumn
    classes = ["collapse"]
    raw_id_fields = ["parent_column", "child_column", "file_control"]
    extra = 0


class NameColumnAdmin(admin.ModelAdmin):
    list_display = [
        "position_in_data",
        "name_in_data",
        #"parameter_group",
        #"final_field__collection",
        "final_field",
        "column_type",
        "parent_column",
        "file_control",
    ]
    raw_id_fields = ["parent_column", "child_column", "file_control"]
    list_filter = [
        "final_field__collection",
        "final_field__parameter_group", "column_type"]
    ordering = ["final_field__collection", "final_field", "name_in_data"]


class FileControlAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "data_group",
        "status_register",
    ]
    list_filter = ["data_group", "petition_file_control__petition__agency"]
    inlines = [
        NameColumnInline,
        PetitionFileControlInline,
    ]


class TransformationAdmin(admin.ModelAdmin):
    list_display = [
        "clean_function",
        "file_control",
        "name_column",
        "addl_params",
    ]
    raw_id_fields = ["name_column", "file_control"]


class DictionaryFileAdmin(admin.ModelAdmin):
    list_display = [
        "institution",
        "delegation",
        "file_control",
        "file",
        "unique_field",
    ]


ocamis_admin_site.register(Transformation, TransformationAdmin)
ocamis_admin_site.register(NameColumn, NameColumnAdmin)
ocamis_admin_site.register(FileControl, FileControlAdmin)
ocamis_admin_site.register(DictionaryFile, DictionaryFileAdmin)
