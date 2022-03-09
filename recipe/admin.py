# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    # RecipeMedicine2,
    # RecipeReport2,
    # RecipeReportLog2,
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


# class RecipeMedicineInline(admin.TabularInline):
#     model = RecipeMedicine
#     extra = 0
#     raw_id_fields = ["container"]


# class RecipeReportAdmin(admin.ModelAdmin):

#     list_display = [
#         "year_month",
#         "clues",
#         "tipo_documento",
#         "folio_documento",
#     ]
#     inlines = [
#         RecipeMedicineInline,
#     ]
#     raw_id_fields = ["clues", "medic"]
#     search_fields = ["tipo_documento", ]

# admin.site.register(RecipeReport, RecipeReportAdmin)


# class RecipeMedicineAdmin(admin.ModelAdmin):
#     list_display = [
#         "recipereport",
#         "container",
#         "cantidad_prescrita",
#         "cantidad_entregada",
#         "precio_medicamento",
#         "rn"]
#     readonly_fields = ["recipereport", "container"]

# admin.site.register(RecipeMedicine, RecipeMedicineAdmin)
