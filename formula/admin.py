from inai.admin import ocamis_admin_site

from django.contrib import admin

from .models import (
    Drug,
    Prescription,
    DocumentType,
    MedicalSpeciality,
    Delivered
)
from med_cat.models import Doctor


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


ocamis_admin_site.register(DocumentType, DocumentTypeAdmin)


class MedicalSpecialityAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


ocamis_admin_site.register(MedicalSpeciality, MedicalSpecialityAdmin)


class DrugInline(admin.TabularInline):
    model = Drug
    extra = 0
    #raw_id_fields = ["container"]


class PrescriptionAdmin(admin.ModelAdmin):

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


ocamis_admin_site.register(Prescription, PrescriptionAdmin)


class DrugAdmin(admin.ModelAdmin):
    list_display = [
        #"prescription",
        "prescribed_amount",
        "delivered_amount",
        "price",
        ]
    #readonly_fields = ["prescription"]


ocamis_admin_site.register(Drug, DrugAdmin)


class DeliveredAdmin(admin.ModelAdmin):
    list_display = [
        "short_name",
        "name",
        "description",
    ]


ocamis_admin_site.register(Delivered, DeliveredAdmin)
