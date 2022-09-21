# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    Report,
    CovidReport,
    Responsable,
    Supply,
    DosisCovid,
    TestimonyMedia,
    #Disease,
    Persona,
    ComplementReport,
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
        "is_covid",
        "emails",
        "update_date",
        #"responsible",
        "position",
        "institution",
        "state",
        "clues",
    ]
    list_filter = ["is_covid", "institution", "state"]
    raw_id_fields = ["clues", ]
    search_fields = [
        "name",
        "emails",
        #"responsible",
        "position",
        "institution__name",
        "state__name",
        "state__short_name",
        "clues__name",
    ]


admin.site.register(Responsable, ResponsableAdmin)


class TestimonyMediaAdmin(admin.ModelAdmin):
    list_display = ["report", "media_file", "url"]
    raw_id_fields = ["report"]


admin.site.register(TestimonyMedia, TestimonyMediaAdmin)


class SupplyAdmin(admin.ModelAdmin):
    list_display = [
        "medicine_name_raw",
        "medicine_type",
        "presentation_raw",
        "medicine_real_name"
    ]
    list_filter = ["medicine_type"]
    raw_id_fields = ["report", "component", "presentation"]
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
    raw_id_fields = ["component", "presentation"]


class DosisInLine(admin.StackedInline):
    model = DosisCovid
    extra = 0
    raw_id_fields = ["state", "municipality"]


class ComplementInLine(admin.StackedInline):
    model = ComplementReport
    extra = 0
    #fields = [
    #    "testimony", "has_corruption", "narration",
    #    "validated", "validator", "validated_date", "pending"]
    fieldsets = [
        [None, {
            "fields": [
                "testimony", "has_corruption", "narration"]}],
        ["Validación y envío", {
            "classes": ["collapse"],
            "fields": [
                "validated", "validator", "validated_date", "pending"]}]]
    show_change_link = True


class TestimonyMediaInLine(admin.StackedInline):
    model = TestimonyMedia
    extra = 0


class TestimonyNullFilterSpec(NullFilterSpec):
    title = u'Testimonio'
    parameter_name = u'testimony'


class ReportAdmin(admin.ModelAdmin):
    model = Report
    list_display = [
        "created", "informer_type", "disease_raw", "state_short_name",
        "clues_clues", "supplies_display"]
    list_filter = ["institution", "state", TestimonyNullFilterSpec]
    readonly_fields = ["created"]
    inlines = [ComplementInLine, SupplyInLine, TestimonyMediaInLine]
    raw_id_fields = ["clues"]

    fieldsets = [
        [None, {
            "fields": [
                "created", "informer_type", "persona",
                "disease_raw", "age"]}],
        [u"Ubicación", {
            "fields": [
                "institution", "institution_raw", "state",
                "hospital_name_raw", "is_other", "clues"]}],
        [u"Mails posteriores", {
            "classes": ["collapse"],
            "fields": [
                "sent_email", "sent_responsible", "want_litigation"]}],
    ]

    def state_short_name(self, obj):
        if obj.state:
            return obj.state.short_name
    state_short_name.short_display = "Estado"

    """def has_testimony(self, obj):
        return True if obj.testimony else False
    has_testimony.short_display = "Tiene testimonio"
    has_testimony.boolean = True"""

    def clues_clues(self, obj):
        return obj.clues.clues if obj.clues else ""
    clues_clues.short_display = "CLUES"

    def supplies_display(self, obj):
        from django.utils.html import format_html_join
        #from django.utils.html import format_html
        #html_list = "",
        #for supp in Supply.objects.filter(report=obj):
        #    html_list += (u'{}<br>' % (supp))
        #return format_html(html_list)
        #return format_html("")
        supplies = Supply.objects.filter(report=obj)
        return format_html_join(
            '\n', "{}{}</br>",
            (('->', supply) for supply in supplies)
        )
    supplies_display.short_display = "Insumos"

    def save_related(self, request, form, formsets, change):
        super(ReportAdmin, self).save_related(request, form, formsets, change)
        obj = form.instance
        obj.send_responsable()

admin.site.register(Report, ReportAdmin)


class CovidReportAdmin(admin.ModelAdmin):
    model = CovidReport
    list_display = [
        "created", "state_short_name", "municipality_name",
        "dosis_display"]
    list_filter = ["state", TestimonyNullFilterSpec]
    readonly_fields = ["created"]
    inlines = [ComplementInLine, DosisInLine]
    raw_id_fields = ["state", "municipality"]

    fieldsets = [
        [None, {
            "fields": [
                "created", "persona"]}],
        [u"Datos de la persona", {
            "fields": [
                "age", "gender", "special_group", "comorbilities"]}],
        [u"Ubicación", {
            "fields": [
                "state", "municipality", "other_location"]}],
    ]

    def state_short_name(self, obj):
        if obj.state:
            return obj.state.short_name
    state_short_name.short_display = "Estado"

    def municipality_name(self, obj):
        if obj.municipality:
            return obj.municipality.name
    municipality_name.short_display = "Municipio"

    """def has_testimony(self, obj):
        return True if obj.testimony else False
    has_testimony.short_display = "Tiene testimonio"
    has_testimony.boolean = True"""

    def dosis_display(self, obj):
        from django.utils.html import format_html
        html_list = ""
        for dosis in DosisCovid.objects.filter(covid_report=obj):
            html_list += (u'%s<br>' % (dosis))
        return format_html(html_list)
    dosis_display.short_display = "Dosis"

admin.site.register(CovidReport, CovidReportAdmin)


class ComplementReportAdmin(admin.ModelAdmin):
    list_display = ["report", "covid_report", "validated"]
    #search_fields = ["name"]

admin.site.register(ComplementReport, ComplementReportAdmin)


class PersonaAdmin(admin.ModelAdmin):
    list_display = ["informer_name", "email", "phone"]
    search_fields = ["informer_name", "email"]


admin.site.register(Persona, PersonaAdmin)


class DosisCovidAdmin(admin.ModelAdmin):
    list_display = ["brand", "round_dosis", "state", "date", "is_success"]
    search_fields = ["brand", "round_dosis", "state"]


admin.site.register(DosisCovid, DosisCovidAdmin)
