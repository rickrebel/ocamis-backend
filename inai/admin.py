from django.contrib import admin
from django.contrib.admin import AdminSite

# Register your models here.
from .models import (
    Petition, FileControl, NameColumn, PetitionFileControl, DataFile, 
    PetitionMonth, ProcessFile)


class OcamisAdminSite(AdminSite):
    site_header = "OCAMIS Admin"
    site_title = "OCAMIS Admin Portal"
    index_title = "Welcome to OCAMIS Portal"

ocamis_admin_site = OcamisAdminSite(name='ocamis_admin')


class DataFileInline(admin.TabularInline):
    model = DataFile
    raw_id_fields = ["petition_file_control", "petition_month"]
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


class PetitionFileControlInline(admin.TabularInline):
    model = PetitionFileControl
    raw_id_fields = ["petition", "file_control"]
    extra = 0


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
    inlines = [ PetitionMonthInline, PetitionFileControlInline ]
    list_filter = ["entity"]

ocamis_admin_site.register(Petition, PetitionAdmin)


class NameColumnInline(admin.StackedInline):
    model = NameColumn
    extra = 0


class FileControlAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "data_group",
        "status_register",
    ]
    list_filter = ["petition_file_control__petition__entity"]
    inlines = [ NameColumnInline, PetitionFileControlInline ]

ocamis_admin_site.register(FileControl, FileControlAdmin)


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition_file_control",
        "file",
        "petition_month",
        "origin_file",
        "status_process",
    ]
    raw_id_fields = ["petition_file_control", "petition_month"]
    list_filter = ["petition_file_control__petition__entity"]

ocamis_admin_site.register(DataFile, DataFileAdmin)


class ProcessFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition",
        "file",
        "file_type",
        "url_download",
    ]
    #raw_id_fields = ["petition_file_control", "month_entity"]
    list_filter = ["petition__entity"]

ocamis_admin_site.register(ProcessFile, ProcessFileAdmin)
