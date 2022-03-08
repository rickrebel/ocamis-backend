# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.filters import SimpleListFilter

"""from .models import (
    # RecipeMedicine,
    # RecipeReport,
    # RecipeReportLog,
    Alliances,
    CLUES,
    Component,
    Container,
    DocumentType,
    Group,
    Institution,
    Medic,
    MedicalSpeciality,
    Presentation,
    PresentationType,
    PurchaseRaw,
    Report,
    Responsable,
    State,
    Supply,
    TestimonyMedia,
    Disease,
)


class DesabastoAdminSite(AdminSite):
    site_header = "Yeeko Desabasto Admin"
    site_title = "Yeeko Desabasto Admin Portal"
    index_title = "Welcome to Yeeko Desabasto Portal"


desabasto_admin_site = DesabastoAdminSite(name='desabasto_admin')


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
    raw_id_fields = ["institution", "state", "clues", ]
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
        "is_national"
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


class TestimonyMediaAdmin(admin.ModelAdmin):
    list_display = ["report", "media_file", "url"]
    raw_id_fields = ["report"]


admin.site.register(TestimonyMedia, TestimonyMediaAdmin)


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
        "clave",
        "official_name",
        "official_attributes",
        "short_attributes",
        "component",
        "presentation_type",
        "presentation_type_raw",
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
    len_short_name_display.short_display = u"Largo del nombre"


admin.site.register(Component, ComponentAdmin)


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
    inlines = [SupplyInLine, TestimonyMediaInLine]
    raw_id_fields = ["clues",  # "validator"
                     ]

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


class PurchaseRawAdmin(admin.ModelAdmin):
    list_display = [
        "raw_pdf",
    ]
    # raw_id_fields = ["presentation"]


admin.site.register(PurchaseRaw, PurchaseRawAdmin)
"""