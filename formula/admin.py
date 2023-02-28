from inai.admin import ocamis_admin_site

from django.contrib import admin

from .models import (
    Drug,
    Prescription,
    DocumentType,
    Doctor,
    MedicalSpeciality,
    Delivered
)


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


ocamis_admin_site.register(DocumentType, DocumentTypeAdmin)


class MedicalSpecialityAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


ocamis_admin_site.register(MedicalSpeciality, MedicalSpecialityAdmin)


class DoctorAdmin(admin.ModelAdmin):

    list_display = ["clave_doctor", "nombre_medico", "especialidad_medico"]
    search_fields = ["clave_doctor", "nombre_medico"]


ocamis_admin_site.register(Doctor, DoctorAdmin)


class DrugInline(admin.TabularInline):
    model = Drug
    extra = 0
    #raw_id_fields = ["container"]


class PrescriptionAdmin(admin.ModelAdmin):

    list_display = [
        #"year_month",
        "clues",
        "document_type",
        "folio_document",
    ]
    inlines = [
        DrugInline,
    ]
    raw_id_fields = ["clues"]
    search_fields = ["document_type", ]


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
