from django.contrib import admin
from django.contrib.admin import register
from rds.models import Cluster, Operation, OperationGroup, MatView
from inai.admin import ocamis_admin_site


@register(Cluster, site=ocamis_admin_site)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name"]


@register(OperationGroup, site=ocamis_admin_site)
class OperationGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "low_priority"]
    # list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["is_active", "low_priority", "name"]
    list_editable = ["is_active", "low_priority"]


@register(Operation, site=ocamis_admin_site)
class OperationAdmin(admin.ModelAdmin):
    list_display = ["operation_type", "order", "low_priority", "is_active",
                    "operation_group", "collection", "script"]
    list_filter = [
        "operation_group", "operation_type", "is_active", "low_priority",
        "collection"]
    search_fields = ["operation_type", "script"]
    ordering = ["-is_active", "order"]
    # list_per_page = 10
    # list_max_show_all = 100
    # list_select_related = ["collection", "mat_view"]
    # list_display_links = ["operation_type", "operation_group"]
    list_editable = ["order", "low_priority", "is_active", "operation_group"]


@register(MatView, site=ocamis_admin_site)
class MatViewAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name", "is_active", "stage_belongs",
                    "stage", "status"]
    list_filter = ["stage_belongs", "is_active"]

