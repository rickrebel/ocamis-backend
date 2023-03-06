from django.contrib import admin
from django.contrib.admin import AdminSite

# from data_param.admin import PetitionFileControlInline, NameColumnAdmin, FileControlAdmin, TransformationAdmin
# Register your models here.
from .models import (
    Petition, PetitionFileControl, DataFile,
    PetitionMonth, ReplyFile)


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
    list_filter = ["petition__entity"]
    inlines = [ DataFileInline ]

ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)


class PetitionMonthInline(admin.TabularInline):
    model = PetitionMonth
    raw_id_fields = ["month_entity"]
    extra = 0


class PetitionAdmin(admin.ModelAdmin):
    list_display = [
        "folio_petition",
        "entity",
        "months",
        "months_in_description",
        "folio_complain",
        "status_data",
        "status_petition",
    ]
    search_fields = [
        "folio_petition", "entity__acronym", "entity__name",
        "entity__state__short_name"]
    inlines = [PetitionMonthInline]
    list_filter = ["entity"]


ocamis_admin_site.register(Petition, PetitionAdmin)


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition_file_control",
        "file",
        "petition_month",
        "origin_file",
        "status_process",
    ]
    raw_id_fields = [
        "petition_file_control", "petition_month", "origin_file",
        "reply_file"]
    list_filter = ["petition_file_control__petition__entity"]


ocamis_admin_site.register(DataFile, DataFileAdmin)


class ReplyFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file",
        "file_type",
        "url_download",
    ]
    raw_id_fields = ["petition"]
    list_filter = ["petition__entity"]


ocamis_admin_site.register(ReplyFile, ReplyFileAdmin)
