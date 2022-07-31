from django.contrib import admin

# Register your models here.
from .models import (
    Petition, FileControl, NameColumn, PetitionFileControl, DataFile)


class PetitionAdmin(admin.ModelAdmin):
    list_display = [
        "entity",
        "status_data",
        "status_petition",
        "folio_petition",
        "folio_complain",
    ]
    list_filter = ["entity"]

admin.site.register(Petition, PetitionAdmin)


class NameColumnInline(admin.TabularInline):
    model = NameColumn
    extra = 0


class PetitionFileControlInline(admin.TabularInline):
    model = PetitionFileControl
    raw_id_fields = ["petition"]
    extra = 0


class FileControlAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "data_group",
        "status_register",
    ]
    list_filter = ["petitions__petition__entity"]
    inlines = [ NameColumnInline, PetitionFileControlInline ]

admin.site.register(FileControl, FileControlAdmin)


class DataFileAdmin(admin.ModelAdmin):
    list_display = [
        "petition_file_control",
        "ori_file",
        "month_entity",
        "origin_file",
        "status_process",
    ]
    list_filter = ["petition_file_control__petition__entity"]

admin.site.register(DataFile, DataFileAdmin)


