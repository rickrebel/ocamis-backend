# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Droug,
    Prescription,
    DocumentType,
    Doctor,
    MedicalSpeciality,
)


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


admin.site.register(DocumentType, DocumentTypeAdmin)


class MedicalSpecialityAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


admin.site.register(MedicalSpeciality, MedicalSpecialityAdmin)


class DoctorAdmin(admin.ModelAdmin):

    list_display = ["clave_doctor", "nombre_medico", "especialidad_medico"]
    search_fields = ["clave_doctor", "nombre_medico"]


admin.site.register(Doctor, DoctorAdmin)


class DrougInline(admin.TabularInline):
    model = Droug
    extra = 0
    #raw_id_fields = ["container"]


class PrescriptionAdmin(admin.ModelAdmin):

    list_display = [
        #"year_month",
        "clues",
        "type_document",
        "folio_documento",
    ]
    inlines = [
        DrougInline,
    ]
    raw_id_fields = ["clues"]
    search_fields = ["type_document", ]

admin.site.register(Prescription, PrescriptionAdmin)


class DrougAdmin(admin.ModelAdmin):
    list_display = [
        "prescription",
        "cantidad_prescrita",
        "cantidad_entregada",
        "precio_medicamento",
        ]
    readonly_fields = ["prescription"]

admin.site.register(Droug, DrougAdmin)
