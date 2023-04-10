from django.contrib import admin
from inai.admin import ocamis_admin_site

from .models import Doctor, Area, Diagnosis, Medicament, MedicalUnit


class DoctorAdmin(admin.ModelAdmin):

    list_display = ["entity", "clave", "full_name", "medical_speciality"]
    search_fields = ["clave", "full_name"]
    list_filter = ["is_aggregate", "entity"]


class AreaAdmin(admin.ModelAdmin):
    list_display = ["entity", "key", "name", "description"]
    search_fields = ["key", "name", "description"]
    list_filter = ["is_aggregate", "entity"]


class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["cie10", "text", "motive"]
    search_fields = ["key", "name"]
    list_filter = ["is_aggregate"]


class MedicamentAdmin(admin.ModelAdmin):
    list_display = ["key2", "own_key2", "component_name",
                    "presentation_description", "container_name", "entity"]
    list_filter = ["entity"]


class MedicalUnitAdmin(admin.ModelAdmin):
    list_display = ["entity", "delegation_name", "name", "clues_key"]
    search_fields = ["clues_key"]
    list_filter = ["entity", "delegation_name"]


ocamis_admin_site.register(Doctor, DoctorAdmin)
ocamis_admin_site.register(Area, AreaAdmin)
ocamis_admin_site.register(Diagnosis, DiagnosisAdmin)
ocamis_admin_site.register(Medicament, MedicamentAdmin)
ocamis_admin_site.register(MedicalUnit, MedicalUnitAdmin)
