from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from inai.admin import ocamis_admin_site
from respond.models import (
    ReplyFile, DataFile, Behavior, SheetFile, CrossingSheet, LapSheet,
    TableFile)


# Register your models here.
class ReplyFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file",
        "url_download",
    ]
    raw_id_fields = ["petition", "month_records"]
    list_filter = ["petition__agency"]


class DataFileInline(admin.TabularInline):
    model = DataFile
    raw_id_fields = ["petition_file_control", "reply_file"]
    extra = 0
    show_change_link = True


class TableFileInline(admin.StackedInline):
    model = TableFile
    extra = 0
    raw_id_fields = [
        "provider", "lap_sheet", "week_record", "iso_delegation", "collection"]
    show_change_link = True


class SheetFileInline(admin.StackedInline):
    model = SheetFile
    extra = 0
    show_change_link = True
    raw_id_fields = ["month_records"]


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
        "provider", "petition_file_control", "reply_file"]
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
    raw_id_fields = ["data_file", "month_records"]


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
        "sheet_file__data_file__provider__acronym", "lap",
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
        "inserted", "collection", "provider__acronym", "year", "month",
        "iso_delegation"]
    search_fields = ["year_month", "year_week"]
    raw_id_fields = ["provider", "lap_sheet", "week_record", "iso_delegation"]


class CrossingSheetAdmin(admin.ModelAdmin):
    list_display = [
        "week_record",
        "month_record",
        "duplicates_count",
        "shared_count",
        "last_crossing",
        "sheet_file_1",
        "sheet_file_2",
    ]
    list_filter = [
        "week_record__provider__acronym", "week_record__year",
        "week_record__month", "week_record__iso_delegation",
        "month_record__provider__acronym", "month_record__year",
        "month_record__month"]
    raw_id_fields = [
        "week_record", "sheet_file_1", "sheet_file_2", "month_record"]
    search_fields = [
        "week_record__year_week", "week_record__year_month",
        "month_record__year_month", "month_record__provider__acronym",
        "week_record__provider__acronym", "week_record__iso_delegation"]


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
ocamis_admin_site.register(DataFile, DataFileAdmin)
ocamis_admin_site.register(SheetFile, SheetFileAdmin)
ocamis_admin_site.register(LapSheet, LapSheetAdmin)
ocamis_admin_site.register(TableFile, TableFileAdmin)
ocamis_admin_site.register(CrossingSheet, CrossingSheetAdmin)
ocamis_admin_site.register(Behavior, BehaviorAdmin)
