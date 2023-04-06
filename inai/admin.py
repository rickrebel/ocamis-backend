from django.contrib import admin
from django.contrib.admin import AdminSite

# from data_param.admin import PetitionFileControlInline, NameColumnAdmin, FileControlAdmin, TransformationAdmin
# Register your models here.
from .models import (
    Petition, PetitionFileControl, DataFile,
    PetitionMonth, ReplyFile, SheetFile, LapSheet)


class OcamisAdminSite(AdminSite):
    site_header = "OCAMIS Admin"
    site_title = "OCAMIS Admin Portal"
    index_title = "Welcome to OCAMIS Portal"


ocamis_admin_site = OcamisAdminSite(name='ocamis_admin')


class DataFileInline(admin.TabularInline):
    model = DataFile
    raw_id_fields = [
        "petition_file_control", "petition_month", "origin_file",
        "reply_file"]
    extra = 0
    show_change_link = True


class PetitionFileControlAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file_control",
    ]
    list_filter = ["petition__agency"]
    inlines = [DataFileInline]

ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)


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


class LapSheetInline(admin.TabularInline):
    model = LapSheet
    extra = 0
    show_change_link = True
    raw_id_fields = ["sheet_file"]


class LapSheetAdmin(admin.ModelAdmin):
    list_display = [
        "sheet_file",
        "lap",
        "inserted",
        "prescription_count",
        "drug_count",
        "total_count",
    ]
    raw_id_fields = ["sheet_file"]


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


class SheetFileInline(admin.StackedInline):
    model = SheetFile
    extra = 0
    show_change_link = True


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition_file_control",
        "file",
        "file_type",
        "suffix",
        "petition_month",
        "origin_file",
        "status_process",
    ]
    raw_id_fields = [
        "petition_file_control", "petition_month", "origin_file",
        "reply_file"]
    list_filter = [
        "file_type",
        "status_process", ("origin_file", admin.EmptyFieldListFilter),
        "petition_file_control__petition__agency"]
    search_fields = [
        "file", "petition_file_control__petition__agency__acronym",
        "petition_file_control__petition__folio_petition"]
    inlines = [SheetFileInline]

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        return list_filter  # + ['origin_file__isnull']


class ReplyFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file",
        "file_type",
        "url_download",
    ]
    raw_id_fields = ["petition"]
    list_filter = ["petition__agency"]


ocamis_admin_site.register(LapSheet, LapSheetAdmin)
ocamis_admin_site.register(Petition, PetitionAdmin)
ocamis_admin_site.register(ReplyFile, ReplyFileAdmin)
ocamis_admin_site.register(DataFile, DataFileAdmin)
ocamis_admin_site.register(SheetFile, SheetFileAdmin)

