# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    Report,
    Responsable,
    Supply,
    TestimonyMedia,
    Disease,
)


class NullFilterSpec(SimpleListFilter):
    title = u''

    parameter_name = u''

    def lookups(self, request, model_admin):
        return (
            ('1', 'Tiene Valor', ),
            ('0', 'Null', ),
        )

    def queryset(self, request, queryset):
        kwargs = {
            '%s' % self.parameter_name: None,
        }
        if self.value() == '0':
            return queryset.filter(**kwargs)
        if self.value() == '1':
            return queryset.exclude(**kwargs)
        return queryset


class ResponsableAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "emails",
        "responsible",
        "position",
        "institution",
        "state",
        "clues",
    ]
    #raw_id_fields = ["institution", "state", "clues", ]
    search_fields = [
        "name",
        "emails",
        "responsible",
        "position",
        "institution__name",
        "state__name",
        "state__short_name",
        "clues__name",
    ]


admin.site.register(Responsable, ResponsableAdmin)


class TestimonyMediaAdmin(admin.ModelAdmin):
    list_display = ["report", "media_file", "url"]
    #raw_id_fields = ["report"]


admin.site.register(TestimonyMedia, TestimonyMediaAdmin)


class SupplyAdmin(admin.ModelAdmin):
    list_display = [
        "medicine_name_raw",
        "medicine_type",
        "presentation_raw",
        "medicine_real_name"
    ]
    list_filter = ["medicine_type"]
    #raw_id_fields = ["report", "component", "presentation"]
    search_fields = [
        "medicine_type",
        "medicine_name_raw",
        "presentation_raw",
        "medicine_real_name"
    ]


admin.site.register(Supply, SupplyAdmin)


class SupplyInLine(admin.StackedInline):
    model = Supply
    extra = 0
    #raw_id_fields = ["component", "presentation"]


class TestimonyMediaInLine(admin.StackedInline):
    model = TestimonyMedia
    extra = 0


class TestimonyNullFilterSpec(NullFilterSpec):
    title = u'Testimonio'
    parameter_name = u'testimony'


class ReportAdmin(admin.ModelAdmin):
    model = Report
    list_display = [
        "created", "trimester", "state_short_name", "hospital_name_raw",
        "clues_clues", "validated", "supplies_display", "origin_app",
        "has_testimony"]
    list_filter = ["institution", "state", TestimonyNullFilterSpec]
    readonly_fields = ["created"]
    #inlines = [SupplyInLine, TestimonyMediaInLine]
    #raw_id_fields = ["clues",  # "validator"
    #                 ]

    fieldsets = [
        [None, {"fields": ["created", "origin_app", "disease_raw", "age"]}],
        [u"Ubicación", {
            "fields": [
                "institution", "institution_raw", "state",
                "hospital_name_raw", "is_other", "clues"]}],
        [u"Informante", {
            "classes": ["collapse"],
            "fields": [
                "informer_name", "email", "phone"]}],
        [u"Memoria escrita", {
            "fields": [
                "testimony", "has_corruption", "narration",
                "want_litigation"]}],
        [u"Validación y envío", {
            "classes": ["collapse"],
            "fields": [
                "validated", "validator", "validated_date", "pending",
                "sent_email", "sent_responsible"]}],
    ]

    def state_short_name(self, obj):
        if obj.state:
            return obj.state.short_name
    state_short_name.short_display = "Estado"

    def has_testimony(self, obj):
        return True if obj.testimony else False
    has_testimony.short_display = "Tiene testimonio"
    has_testimony.boolean = True

    def clues_clues(self, obj):
        return obj.clues.clues if obj.clues else ""
    clues_clues.short_display = "CLUES"

    def supplies_display(self, obj):
        from django.utils.html import format_html
        html_list = ""
        for supplies in Supply.objects.filter(report=obj):
            html_list += (u'%s<br>' % (supplies))
        return format_html(html_list)
    supplies_display.short_display = "Insumos"

    def save_related(self, request, form, formsets, change):
        super(ReportAdmin, self).save_related(request, form, formsets, change)
        obj = form.instance
        obj.send_responsable()


admin.site.register(Report, ReportAdmin)


class DiseaseAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]
    search_fields = ["name"]


admin.site.register(Disease, DiseaseAdmin)
