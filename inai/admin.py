from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import (
    Petition, PetitionFileControl, EntityMonth, EntityWeek, RequestTemplate,
    Variable)


class OcamisAdminSite(AdminSite):
    site_header = "OCAMIS Admin"
    site_title = "OCAMIS Admin Portal"
    index_title = "Welcome to OCAMIS Portal"


ocamis_admin_site = OcamisAdminSite(name='ocamis_admin')


# class PetitionMonthInline(admin.TabularInline):
#     model = PetitionMonth
#     raw_id_fields = ["entity_month"]
#     extra = 0


class EntityWeekInline(admin.TabularInline):
    model = EntityWeek
    raw_id_fields = ["provider", "entity_month", "iso_delegation"]
    extra = 0


class EntityWeekAdmin(admin.ModelAdmin):
    from respond.admin import TableFileInline
    list_display = [
        "id",
        "entity_month",
        "year_week",
        "year_month",
        "iso_delegation",
        "drugs_count",
        "rx_count",
        "duplicates_count",
    ]
    list_filter = ["provider__acronym", "year", "month"]
    raw_id_fields = ["provider", "entity_month", "iso_delegation"]
    inlines = [TableFileInline]
    search_fields = [
        "provider__acronym", "provider__state__short_name",
        "year_week", "year_month", "iso_delegation__name"]


class EntityMonthAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "provider",
        "year_month",
        "agency",
    ]
    raw_id_fields = ["provider", "agency"]
    filter_horizontal = ["petition"]
    list_filter = ["provider__acronym", "year_month"]
    # inlines = [EntityWeekInline]


# class EntityMonthInline(admin.TabularInline):
#     model = EntityMonth
#     raw_id_fields = ["provider"]
#     extra = 0


class PetitionAdmin(admin.ModelAdmin):
    list_display = [
        "folio_petition",
        "agency",
        "months",
        "months_in_description",
        "folio_complain",
        "status_data",
        "status_petition",
    ]
    search_fields = [
        "folio_petition", "agency__acronym", "agency__name",
        "agency__state__short_name"]
    raw_id_fields = ["entity_months"]
    # inlines = [EntityMonthInline]
    list_filter = ["agency"]


class PetitionFileControlAdmin(admin.ModelAdmin):
    from respond.admin import DataFileInline
    list_display = [
        "petition",
        "file_control",
    ]
    list_filter = ["petition__agency"]
    raw_id_fields = ["petition", "file_control"]
    inlines = [DataFileInline]


ocamis_admin_site.register(Petition, PetitionAdmin)
ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)

ocamis_admin_site.register(EntityMonth, EntityMonthAdmin)
ocamis_admin_site.register(EntityWeek, EntityWeekAdmin)

