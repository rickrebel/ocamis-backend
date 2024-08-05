from inai.admin import ocamis_admin_site

from django.contrib import admin

from .models import (
    CLUES,
    Institution,
    State,
    Municipality,
    Agency,
    Delegation,
    Provider
)


class StateAdmin(admin.ModelAdmin):
    list_display = [
        "inegi_code",
        "name",
        "short_name",
        "code_name",
        "other_names"]
    search_fields = [
        "inegi_code",
        "name",
        "short_name",
        "code_name",
        "other_names"]


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = [
        "inegi_code",
        "name"]
    search_fields = [
        "inegi_code",
        "name"]


class InstitutionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "public_name",
        "public_code",
        "relevance"]
    search_fields = [
        "name",
        "code",
        "public_name",
        "public_code",
        "relevance"]


class AgencyInline(admin.StackedInline):
    model = Agency
    raw_id_fields = ["clues"]
    extra = 0


class ProviderAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "acronym",
        "state",
        "institution",
        "is_clues",
        "population",
    ]
    inlines = [AgencyInline]
    list_filter = ["is_clues", "institution"]


class CLUESAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "clues",
        "is_searchable",
        "typology",
        "state",
        "jurisdiction",
        "municipality",
        "is_national",
        "total_unities",
    ]
    list_filter = [
        "is_searchable",
        "is_national",
        "institution",
        "state"
    ]
    raw_id_fields = [
        "state", "institution", "municipality", "delegation", "provider"]
    search_fields = [
        "name",
        "institution__name",
        "institution__code",
        "state__name",
        "state__short_name",
        "clues",
        "typology_cve",
        "typology",
        "jurisdiction"
    ]


class AgencyAdmin(admin.ModelAdmin):
    list_display = [
        "acronym",
        "name",
        "provider",
        "agency_type",
        "vigencia",
        "competent",
        "nombreSujetoObligado",
        "state",
        "institution",
        "clues",
        "is_pilot"
    ]
    raw_id_fields = ["clues", "state", "provider"]
    list_editable = ["nombreSujetoObligado", "competent", "is_pilot"]
    search_fields = [
        "acronym",
        "name",
        "provider__acronym",
        "provider__name",
        "institution__code",
        "state__short_name"
    ]


class DelegationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "state",
        "institution",
    ]
    search_fields = [
        "name",
        "institution__code",
        "institution__name",
        "state__short_name"
    ]
    list_filter = ["state", "institution"]


admin.site.register(State, StateAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
admin.site.register(Institution, InstitutionAdmin)
ocamis_admin_site.register(Institution, InstitutionAdmin)
ocamis_admin_site.register(Provider, ProviderAdmin)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(CLUES, CLUESAdmin)

ocamis_admin_site.register(Agency, AgencyAdmin)
admin.site.register(Agency, AgencyAdmin)

ocamis_admin_site.register(Delegation, DelegationAdmin)
admin.site.register(Delegation, DelegationAdmin)
