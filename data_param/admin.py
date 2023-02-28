from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction, 
    ParameterGroup)


class CleanFunctionInLine(admin.StackedInline):
    model = CleanFunction
    extra = 0
    show_change_link = True


class FinalFieldAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "collection",
        "parameter_group",
        "verbose_name",
        "data_type",
        "in_data_base",
        "is_common",
        "verified",
        "need_for_viz",
        "is_unique",
    ]
    list_filter = ["collection", "parameter_group", "data_type"]
    inlines = [CleanFunctionInLine]
    list_editable = [
        "verified",
        "verbose_name",
        "in_data_base",
        "is_common",
        "need_for_viz",
        "is_unique",
    ]
    ordering = [
        "parameter_group", "collection", "-is_common", "verbose_name"]        
    search_fields = [
        "name", "collection__name", "collection__model_name",
        "verbose_name", "parameter_group__name"]

ocamis_admin_site.register(FinalField, FinalFieldAdmin)


class FinalFieldInLine(admin.StackedInline):
    model = FinalField
    extra = 0
    show_change_link = True
    fieldsets=(
        (None, {
            "fields":("collection","name","verbose_name","data_type","addl_params",)
        }),
        ("Más configuraciones:", {
            #"classes": ("collapse",),
            "fields": ("variations", "is_required", "is_common", "dashboard_hide", "in_data_base", "verified")
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
        "color",
    ]
    list_editable = ["color"]
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
