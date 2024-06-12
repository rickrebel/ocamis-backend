from django.contrib import admin
from django.contrib.admin import AdminSite, register
from rds.models import Cluster
from inai.admin import ocamis_admin_site


@register(Cluster, site=ocamis_admin_site)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ["name", "public_name", "display_providers"]


