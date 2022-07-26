from django.contrib import admin

# Register your models here.
from .models import (
    #GroupParameter,
    DataGroup, Collection, FinalField, DataType, CleanFunction)


admin.site.register(DataGroup)


class CollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "model_name"]

admin.site.register(Collection, CollectionAdmin)


class FinalFieldAdmin(admin.ModelAdmin):
    list_display = ["name", "collection", "verbose_name", "data_type"]
    search_fields = [
        "name", "collection__name", "collection__model_name", "verbose_name"]

admin.site.register(FinalField, FinalFieldAdmin)


class DataTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "addl_params", "is_common", "order"]

admin.site.register(DataType, DataTypeAdmin)


class CleanFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "public_name", "for_all_data", "restricted_field",
        "priority"]

admin.site.register(CleanFunction, CleanFunctionAdmin)
