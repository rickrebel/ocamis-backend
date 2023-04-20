from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import (
    Petition, PetitionFileControl, DataFile,
    PetitionMonth, ReplyFile, SheetFile, LapSheet, TableFile)


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
    raw_id_fields = [
        "petition_file_control", "petition_month", "origin_file",
        "reply_file"]
    extra = 0
    show_change_link = True


class PetitionMonthInline(admin.TabularInline):
    model = PetitionMonth
    raw_id_fields = ["month_agency"]
    extra = 0


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
    inlines = [PetitionMonthInline]
    list_filter = ["agency"]


class PetitionFileControlAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file_control",
    ]
    list_filter = ["petition__agency"]
    inlines = [DataFileInline]


class SheetFileInline(admin.StackedInline):
    model = SheetFile
    extra = 0
    show_change_link = True


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "file_type",
        # "petition_file_control",
        "file",
        "suffix",
        "stage",
        "status",
    ]
    raw_id_fields = [
        "petition_file_control", "petition_month", "origin_file",
        "reply_file"]
    list_filter = [
        "file_type", "stage", "status",
        # ("origin_file", admin.EmptyFieldListFilter),
        "petition_file_control__petition__agency"]
    search_fields = [
        "file", "petition_file_control__petition__agency__acronym",
        "petition_file_control__petition__folio_petition"]
    inlines = [SheetFileInline]

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        return list_filter  # + ['origin_file__isnull']


class TableFileInline(admin.TabularInline):
    model = TableFile
    extra = 0
    raw_id_fields = ["lap_sheet"]
    show_change_link = True


class LapSheetInline(admin.StackedInline):
    model = LapSheet
    extra = 0
    show_change_link = True
    raw_id_fields = ["sheet_file"]
    inlines = [TableFileInline]


class SheetFileAdmin(admin.ModelAdmin):
    list_display = [
        "file",
        "file_type",
        "matched",
        "sheet_name",
    ]
    list_filter = [
        "file_type", "matched"]
    search_fields = [
        "file", "data_file__petition__agency__acronym",
        "data_file__petition__folio_petition"]
    inlines = [LapSheetInline]
    raw_id_fields = ["data_file"]


class LapSheetAdmin(admin.ModelAdmin):
    list_display = [
        "last_edit",
        "lap",
        "inserted",
        "prescription_count",
        "drug_count",
        "total_count",
        "sheet_file",
    ]
    inlines = [TableFileInline]
    raw_id_fields = ["sheet_file"]


class TableFileAdmin(admin.ModelAdmin):

    list_display = [
        "collection",
        "file",
        "lap_sheet",
    ]
    list_filter = ["collection"]
    raw_id_fields = ["lap_sheet"]


ocamis_admin_site.register(ReplyFile, ReplyFileAdmin)
ocamis_admin_site.register(Petition, PetitionAdmin)
ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)
ocamis_admin_site.register(DataFile, DataFileAdmin)
ocamis_admin_site.register(SheetFile, SheetFileAdmin)
ocamis_admin_site.register(LapSheet, LapSheetAdmin)
ocamis_admin_site.register(TableFile, TableFileAdmin)
