from django.contrib import admin

from .models import Doctor, Area, Diagnosis, Medicament, MedicalUnit


class DoctorAdmin(admin.ModelAdmin):

    list_display = ["provider", "clave", "full_name", "medical_speciality"]
    search_fields = ["clave", "full_name"]
    list_filter = ["is_aggregate", "provider"]


class AreaAdmin(admin.ModelAdmin):
    list_display = ["provider", "key", "name", "description"]
    search_fields = ["key", "name", "description"]
    list_filter = ["is_aggregate", "provider"]


class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["cie10", "text", "motive"]
    search_fields = ["key", "name"]
    list_filter = ["is_aggregate"]


class MedicamentAdmin(admin.ModelAdmin):
    list_display = [
        "key2", "own_key2", "component_name",
        "presentation_description", "container_name", "provider"]
    list_filter = ["provider"]
    raw_id_fields = ["provider", "component", "presentation", "container"]


class MedicalUnitAdmin(admin.ModelAdmin):
    list_display = ["provider", "delegation_name", "name", "clues_key"]
    search_fields = ["clues_key"]
    list_filter = ["provider", "delegation_name"]


admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Diagnosis, DiagnosisAdmin)
admin.site.register(Medicament, MedicamentAdmin)
admin.site.register(MedicalUnit, MedicalUnitAdmin)
