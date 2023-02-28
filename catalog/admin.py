# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from inai.admin import ocamis_admin_site

from django.contrib import admin
#from django.contrib.admin import AdminSite

from .models import (
    Alliances,
    CLUES,
    Institution,
    State,
    Municipality,
    Disease,
    Entity,
    Delegation,
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

admin.site.register(State, StateAdmin)
ocamis_admin_site.register(State, StateAdmin)


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = [
        "inegi_code",
        "name"]
    search_fields = [
        "inegi_code",
        "name"]


admin.site.register(Municipality, MunicipalityAdmin)


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

admin.site.register(Institution, InstitutionAdmin)
ocamis_admin_site.register(Institution, InstitutionAdmin)


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
    raw_id_fields = ["state", "institution"]
    search_fields = [
        "name",
        "institution__name",
        "institution__code",
        "state__name",
        "state__short_name",
        "clues",
        "typology_cve",
        "jurisdiction"
    ]

admin.site.register(CLUES, CLUESAdmin)
ocamis_admin_site.register(CLUES, CLUESAdmin)


class AlliancesAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "page_url",
        "logo",
        "level",
    ]
    search_fields = ["name"]


admin.site.register(Alliances, AlliancesAdmin)


class DiseaseAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]
    search_fields = ["name"]

admin.site.register(Disease, DiseaseAdmin)


class EntityAdmin(admin.ModelAdmin):
    list_display = [
        "acronym",
        "name",
        "entity_type",
        "vigencia",
        "competent",
        "nombreSujetoObligado",
        "state",
        "institution",
        "clues",
        "is_pilot"]
    raw_id_fields = ["clues"]
    list_editable = ["nombreSujetoObligado", "competent", "is_pilot"]
    search_fields = [
        "acronym",
        "name",
        "institution__code",
        "state__short_name"
        ]

#admin.site.register(Entity, EntityAdmin)
ocamis_admin_site.register(Entity, EntityAdmin)


class DelegationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "state",
        "institution",
        "clues",
    ]
    raw_id_fields = ["clues"]
    search_fields = [
        "name",
        "institution__code",
        "institution__name",
        "state__short_name"
    ]


ocamis_admin_site.register(Delegation, DelegationAdmin)
