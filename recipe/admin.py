# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Medicine,
    Recipe,
    # RecipeLog2,
    DocumentType,
    Medic,
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


class MedicAdmin(admin.ModelAdmin):

    list_display = ["clave_medico", "nombre_medico", "especialidad_medico"]
    search_fields = ["clave_medico", "nombre_medico"]


admin.site.register(Medic, MedicAdmin)


class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 0
    #raw_id_fields = ["container"]


class RecipeAdmin(admin.ModelAdmin):

    list_display = [
        #"year_month",
        "clues",
        "type_document",
        "folio_documento",
    ]
    inlines = [
        MedicineInline,
    ]
    raw_id_fields = ["clues"]
    search_fields = ["type_document", ]

admin.site.register(Recipe, RecipeAdmin)


class MedicineAdmin(admin.ModelAdmin):
    list_display = [
        "recipe",
        "cantidad_prescrita",
        "cantidad_entregada",
        "precio_medicamento",
        ]
    readonly_fields = ["recipe"]

admin.site.register(Medicine, MedicineAdmin)
