# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
#from django.contrib.admin import AdminSite

from .models import (
    Alliances,
    CLUES,
    Institution,
    State,
    Municipality,
    Disease,
    Entity
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


class EntityAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "institution",
        "state",
        "clues"]
    raw_id_fields = ["clues"]

    search_fields = [
        "name",
        "institution__code",
        "state__short_name"
        ]

admin.site.register(Entity, EntityAdmin)


admin.site.register(State, StateAdmin)


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


class CLUESAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "clues",
        "is_searchable",
        "tipology",
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
        "state__name",
        "state__short_name",
        "clues",
        "jurisdiction"
    ]

admin.site.register(CLUES, CLUESAdmin)


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
