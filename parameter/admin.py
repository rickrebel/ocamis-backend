from django.contrib import admin

# Register your models here.
from .models import (
    GroupParameter, GroupData, Collection, FinalField, TypeData)


class GroupParameterAdmin(admin.ModelAdmin):
    list_display = ["name", "group_data"]

admin.site.register(GroupParameter, GroupParameterAdmin)


admin.site.register(GroupData)


class CollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "model_name"]

admin.site.register(Collection, CollectionAdmin)


class FinalFieldAdmin(admin.ModelAdmin):
    list_display = ["name", "collection", "verbose_name", "type_data"]
    search_fields = [
        "name", "collection__name", "collection__model_name", "verbose_name"]

admin.site.register(FinalField, FinalFieldAdmin)


class TypeDataAdmin(admin.ModelAdmin):
    list_display = ["name", "addl_params", "is_common", "order"]

admin.site.register(TypeData, TypeDataAdmin)
