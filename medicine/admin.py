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


class PresentationInline(admin.StackedInline):
    model = Presentation
    extra = 0
    show_change_link = True


class ComponentInline(admin.StackedInline):
    model = Component
    extra = 0
    show_change_link = True


class GroupAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "need_survey"]
    # inlines = [ComponentInline]
    search_fields = ["name", "alias"]


class ComponentAdmin(admin.ModelAdmin):
    list_display = [
        "name", "interactions", "priority", "groups_count", "groups_pc_count",
        "presentations_count", "containers_count", "frequency"]
    inlines = [PresentationInline]
    search_fields = ["name", "alias", "short_name"]
    list_filter = ["origen_cvmei", "is_vaccine", "priority"]

    def len_short_name_display(self, obj):
        return obj.len_short_name
    len_short_name_display.short_display = "Largo del nombre"


class ContainerInline(admin.StackedInline):
    model = Container
    # raw_id_fields = ["presentation"]
    show_change_link = True
    extra = 0


class PresentationAdmin(admin.ModelAdmin):
    list_display = [
        "description",
        "component",
        "presentation_type",
    ]
    list_filter = ["origen_cvmei", "group", "presentation_type"]
    raw_id_fields = ["component"]
    search_fields = [
        "description",
        "presentation_type_raw",
        "clave",
        "official_name",
        "official_attributes",
        "short_attributes",
    ]
    inlines = [ContainerInline]


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
    search_fields = [
        "name", "key", "short_name", "key2",
        "presentation__component__name",
        "presentation__description"]


admin.site.register(PresentationType, PresentationTypeAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(Presentation, PresentationAdmin)
admin.site.register(Container, ContainerAdmin)
