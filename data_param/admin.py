from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction)


class FinalFieldAdmin(admin.ModelAdmin):
    list_display = [
        "collection",
        "name",
        "verbose_name",
        "data_type",
        "verified",
    ]
    list_filter = ["collection", "data_type"]
    search_fields = [
        "name", "collection__name", "collection__model_name",
        "verbose_name"]

ocamis_admin_site.register(FinalField, FinalFieldAdmin)


class FinalFieldInline(admin.TabularInline):
    model = FinalField
    extra = 0


class CollectionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model_name",
        "data_group",
        "description",
    ]
    inlines = [
        FinalFieldInline,
    ]

ocamis_admin_site.register(Collection, CollectionAdmin)


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0


class DataGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_default",
    ]
    inlines = [ CollectionInline ]

ocamis_admin_site.register(DataGroup, DataGroupAdmin)



class DataTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "is_common",
        "order",
    ]

ocamis_admin_site.register(DataType, DataTypeAdmin)



class CleanFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "public_name", "for_all_data", "restricted_field",
        "priority"]

ocamis_admin_site.register(CleanFunction, CleanFunctionAdmin)
