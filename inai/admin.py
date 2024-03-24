from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    Petition, PetitionFileControl, EntityMonth, EntityWeek)
from respond.models import ReplyFile, DataFile, Behavior, SheetFile, CrossingSheet, LapSheet, TableFile


class OcamisAdminSite(AdminSite):
    site_header = "OCAMIS Admin"
    site_title = "OCAMIS Admin Portal"
    index_title = "Welcome to OCAMIS Portal"


ocamis_admin_site = OcamisAdminSite(name='ocamis_admin')


class ReplyFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file",
        "file_type",
        "url_download",
    ]
    raw_id_fields = ["petition"]
    list_filter = ["petition__agency"]


class DataFileInline(admin.TabularInline):
    model = DataFile
    raw_id_fields = ["petition_file_control", "reply_file"]
    extra = 0
    show_change_link = True


# class PetitionMonthInline(admin.TabularInline):
#     model = PetitionMonth
#     raw_id_fields = ["entity_month"]
#     extra = 0

class TableFileInline(admin.StackedInline):
    model = TableFile
    extra = 0
    raw_id_fields = [
        "entity", "lap_sheet", "entity_week", "iso_delegation", "collection"]
    show_change_link = True


class EntityWeekInline(admin.TabularInline):
    model = EntityWeek
    raw_id_fields = ["entity", "entity_month", "iso_delegation"]
    extra = 0


class EntityWeekAdmin(admin.ModelAdmin):
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
    list_filter = ["entity__acronym", "year", "month"]
    raw_id_fields = ["entity", "entity_month", "iso_delegation"]
    inlines = [TableFileInline]
    search_fields = [
        "entity__acronym", "entity__state__short_name",
        "year_week", "year_month", "iso_delegation__name"]


class EntityMonthAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "entity",
        "year_month",
        "agency",
    ]
    raw_id_fields = ["entity", "agency"]
    filter_horizontal = ["petition"]
    list_filter = ["entity__acronym", "year_month"]
    # inlines = [EntityWeekInline]


# class EntityMonthInline(admin.TabularInline):
#     model = EntityMonth
#     raw_id_fields = ["entity"]
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
    list_display = [
        "petition",
        "file_control",
    ]
    list_filter = ["petition__agency"]
    raw_id_fields = ["petition", "file_control"]
    inlines = [DataFileInline]


class SheetFileInline(admin.StackedInline):
    model = SheetFile
    extra = 0
    show_change_link = True
    raw_id_fields = ["entity_months"]


class NullFilterField(SimpleListFilter):
    title = "Tiene pet_file_control"

    parameter_name = 'has_field'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Sí Tiene', ),
            ('0', 'No tiene', ),
        )

    def queryset(self, request, queryset):
        kwargs = {'petition_file_control__isnull': True}
        # kwargs = {'%s' % self.parameter_name: None}
        if self.value() == '0':
            return queryset.filter(**kwargs)
        if self.value() == '1':
            return queryset.exclude(**kwargs)
        return queryset


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "file",
        "suffix",
        "stage",
        "status",
    ]
    raw_id_fields = [
        "entity", "petition_file_control", "reply_file"]
    list_filter = [
        NullFilterField, "stage", "status",
        "petition_file_control__petition__agency"]
    search_fields = [
        "file", "petition_file_control__petition__agency__acronym",
        "petition_file_control__petition__folio_petition"]
    inlines = [SheetFileInline]

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        return list_filter


class LapSheetInline(admin.StackedInline):
    model = LapSheet
    extra = 0
    show_change_link = True
    raw_id_fields = ["sheet_file"]
    inlines = [TableFileInline]


class SheetFileAdmin(admin.ModelAdmin):
    list_display = [
        "file_type",
        "file",
        "matched",
        "sheet_name",
        "behavior",
        "total_rows",
    ]
    list_filter = ["file_type", "matched"]
    search_fields = [
        "file", "data_file__petition_file_control__petition__agency__acronym",
        "data_file__petition_file_control__petition__folio_petition"]
    inlines = [LapSheetInline]
    raw_id_fields = ["data_file", "entity_months"]


class LapSheetAdmin(admin.ModelAdmin):
    list_display = [
        "last_edit",
        "lap",
        "inserted",
        "rx_count",
        "drugs_count",
        "total_count",
        "sheet_file",
    ]
    inlines = [TableFileInline]
    search_fields = [
        # "sheet_file__filename",
        # "sheet_file__data_file__file",
        "sheet_file__data_file_id"]
    list_filter = [
        "sheet_file__data_file__entity__acronym", "lap",
        "inserted", "cat_inserted", "missing_inserted"]
    raw_id_fields = ["sheet_file"]


class TableFileAdmin(admin.ModelAdmin):

    list_display = [
        "collection",
        "year_month",
        "year_week",
        "rx_count",
        "drugs_count",
        "lap_sheet",
        "file",
    ]
    list_filter = [
        "inserted", "entity__acronym", "collection", "year", "month",
        "iso_delegation"]
    search_fields = ["year_month", "year_week"]
    raw_id_fields = ["entity", "lap_sheet", "entity_week", "iso_delegation"]


class CrossingSheetAdmin(admin.ModelAdmin):
    list_display = [
        "entity_week",
        "entity_month",
        "duplicates_count",
        "shared_count",
        "last_crossing",
        "sheet_file_1",
        "sheet_file_2",
    ]
    list_filter = [
        "entity_week__entity__acronym", "entity_week__year",
        "entity_week__month", "entity_week__iso_delegation",
        "entity_month__entity__acronym", "entity_month__year",
        "entity_month__month"]
    raw_id_fields = [
        "entity_week", "sheet_file_1", "sheet_file_2", "entity_month"]
    search_fields = [
        "entity_week__year_week", "entity_week__year_month",
        "entity_month__year_month", "entity_month__entity__acronym",
        "entity_week__entity__acronym", "entity_week__iso_delegation"]


class BehaviorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "public_name",
        "description",
        "icon",
        "is_valid",
        "is_discarded",
        "is_merge",
    ]


ocamis_admin_site.register(ReplyFile, ReplyFileAdmin)
ocamis_admin_site.register(Petition, PetitionAdmin)
ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)
ocamis_admin_site.register(DataFile, DataFileAdmin)
ocamis_admin_site.register(SheetFile, SheetFileAdmin)
ocamis_admin_site.register(LapSheet, LapSheetAdmin)
ocamis_admin_site.register(TableFile, TableFileAdmin)
ocamis_admin_site.register(CrossingSheet, CrossingSheetAdmin)
ocamis_admin_site.register(Behavior, BehaviorAdmin)
ocamis_admin_site.register(EntityMonth, EntityMonthAdmin)
ocamis_admin_site.register(EntityWeek, EntityWeekAdmin)

