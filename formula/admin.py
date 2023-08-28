from django.contrib import admin

from .models import (
    Drug,
    Rx,
    DocumentType,
)
from med_cat.models import Doctor, Delivered


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


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


class DrugAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "rx",
        "sheet_file_id",
        "prescribed_amount",
        "delivered_amount",
        "price",
    ]
    readonly_fields = [
        "rx", "sheet_file_id", "lap_sheet_id", "medicament", "delivered"]


class DeliveredAdmin(admin.ModelAdmin):
    list_display = [
        "hex_hash",
        "name",
        "description",
    ]


admin.site.register(DocumentType, DocumentTypeAdmin)
admin.site.register(Rx, RxAdmin)
admin.site.register(Drug, DrugAdmin)
admin.site.register(Delivered, DeliveredAdmin)
