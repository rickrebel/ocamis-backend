# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Component,
    Container,
    Group,
    Presentation,
    PresentationType,
)


class PresentationTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "common_name", "alias"]
    list_filter = ["origen_cvmei"]
    raw_id_fields = ["agrupated_in"]
    search_fields = ["name", "common_name", "alias"]


admin.site.register(PresentationType, PresentationTypeAdmin)


admin.site.register(Group)


class ContainerAdmin(admin.ModelAdmin):
    list_display = [
        "presentation",
        "name",
        "key",
        "is_current",
        "short_name",
    ]
    list_filter = ["is_current", "origen_cvmei"]
    raw_id_fields = ["presentation"]
    search_fields = ["name", "key", "short_name"]


admin.site.register(Container, ContainerAdmin)


class PresentationAdmin(admin.ModelAdmin):
    list_display = [
        "description",
        "component",
        "presentation_type",
    ]
    list_filter = ["origen_cvmei"]
    raw_id_fields = ["component"]
    search_fields = [
        "description",
        "presentation_type_raw",
        "clave",
        "official_name",
        "official_attributes",
        "short_attributes",
    ]


admin.site.register(Presentation, PresentationAdmin)


class PresentationInline(admin.StackedInline):
    model = Presentation
    extra = 0


class ComponentAdmin(admin.ModelAdmin):
    list_display = [
        "short_name", "alias", "frequency", "is_vaccine",
        "len_short_name_display"]
    inlines = [
        PresentationInline
    ]
    search_fields = ["name", "alias", "short_name"]
    list_filter = ["origen_cvmei", "is_vaccine"]

    def len_short_name_display(self, obj):
        return obj.len_short_name
    len_short_name_display.short_display = "Largo del nombre"


admin.site.register(Component, ComponentAdmin)
