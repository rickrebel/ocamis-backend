from inai.admin import ocamis_admin_site

from django.contrib import admin

from .models import (
    Drug,
    Rx,
    DocumentType,
    # MedicalSpeciality,
)
from med_cat.models import Doctor, Delivered


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


ocamis_admin_site.register(DocumentType, DocumentTypeAdmin)


class DrugInline(admin.TabularInline):
    model = Drug
    extra = 0
    # raw_id_fields = ["container"]


class RxAdmin(admin.ModelAdmin):

    list_display = [
        "entity",
        "folio_document",
        "delivered_final",
        "iso_year",
        "month",
        "medical_unit",
        "document_type",
        "doctor",
        "diagnosis",
    ]
    inlines = [
        DrugInline,
    ]
    raw_id_fields = ["entity", "medical_unit", "area", "doctor", "diagnosis"]
    list_filter = ["entity", "iso_year", "month"]
    search_fields = ["folio_document", ]


ocamis_admin_site.register(Rx, RxAdmin)


class DrugAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "rx",
        "sheet_file",
        "prescribed_amount",
        "delivered_amount",
        "price",
    ]
    readonly_fields = [
        "rx", "sheet_file", "lap_sheet", "medicament", "delivered"]


ocamis_admin_site.register(Drug, DrugAdmin)


class DeliveredAdmin(admin.ModelAdmin):
    list_display = [
        "hex_hash",
        "name",
        "description",
    ]


ocamis_admin_site.register(Delivered, DeliveredAdmin)
