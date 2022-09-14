from django.contrib import admin
from django.contrib.admin import AdminSite

# Register your models here.
from .models import (
    Petition, FileControl, NameColumn, PetitionFileControl, DataFile, 
    PetitionMonth, ProcessFile, Transformation)


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
    search_fields = [
        "folio_petition", "entity__acronym", "entity__name",
        "entity__state__short_name"]
    inlines = [ PetitionMonthInline, PetitionFileControlInline ]
    list_filter = ["entity"]

ocamis_admin_site.register(Petition, PetitionAdmin)


class NameColumnInline(admin.StackedInline):
    model = NameColumn
    classes = ["collapse"]
    raw_id_fields = ["parent_column", "children_column"]
    extra = 0


class NameColumnAdmin(admin.ModelAdmin):
    list_display = [
        "position_in_data",
        "name_in_data",
        #"parameter_group",
        #"final_field__collection",
        "final_field",
        "column_type",
        "parent_column",
        "file_control"
    ]
    raw_id_fields = ["parent_column", "children_column"]
    list_filter = [
        "final_field__collection", 
        "final_field__parameter_group", "column_type"]
    ordering = ["collection", "final_field", "name_in_data"]


ocamis_admin_site.register(NameColumn, NameColumnAdmin)


class FileControlAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "data_group",
        "status_register",
    ]
    list_filter = ["petition_file_control__petition__entity"]
    inlines = [
        NameColumnInline,
        PetitionFileControlInline,
    ]

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


class TransformationAdmin(admin.ModelAdmin):
    list_display = [
        "clean_function",
        "file_control",
        "name_column",
        "addl_params",
    ]

ocamis_admin_site.register(Transformation, TransformationAdmin)


