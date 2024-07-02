from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import (
    Petition, PetitionFileControl, MonthRecord, WeekRecord, RequestTemplate,
    Variable, Complaint)


class OcamisAdminSite(AdminSite):
    site_header = "OCAMIS Admin"
    site_title = "OCAMIS Admin Portal"
    index_title = "Welcome to OCAMIS Portal"


ocamis_admin_site = OcamisAdminSite(name='ocamis_admin')


# class PetitionMonthInline(admin.TabularInline):
#     model = PetitionMonth
#     raw_id_fields = ["month_record"]
#     extra = 0


class WeekRecordInline(admin.TabularInline):
    model = WeekRecord
    raw_id_fields = ["provider", "month_record", "iso_delegation"]
    extra = 0


class WeekRecordAdmin(admin.ModelAdmin):
    from respond.admin import TableFileInline
    list_display = [
        "id",
        "month_record",
        "year_week",
        "year_month",
        "iso_delegation",
        "drugs_count",
        "rx_count",
        "duplicates_count",
    ]
    list_filter = ["provider__acronym", "year", "month"]
    raw_id_fields = ["provider", "month_record", "iso_delegation"]
    inlines = [TableFileInline]
    search_fields = [
        "provider__acronym", "provider__state__short_name",
        "year_week", "year_month", "iso_delegation__name"]


class MonthRecordAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "provider",
        "year_month",
        "agency",
    ]
    raw_id_fields = ["provider", "agency"]
    filter_horizontal = ["petition"]
    list_filter = ["provider__acronym", "year_month"]
    search_fields = [
        "provider__acronym", "provider__state__short_name", "year_month"]
    # inlines = [WeekRecordInline]


class ComplaintInline(admin.StackedInline):
    model = Complaint
    extra = 0


class PetitionAdmin(admin.ModelAdmin):
    list_display = [
        "folio_petition",
        "agency",
        "months",
        "months_in_description",
        "status_data",
        "status_petition",
    ]
    fieldsets = (
        (None, {
            "fields": (
                "folio_petition",
                "id_inai_open_data",
                "agency",
                "real_provider",
                "month_records",
                "notes",
                # "template_text",
                # "request_template",
                "send_petition",
                "response_limit",
                "send_response",
                "description_petition",
                "description_response",
                "status_petition",
                "status_data",
                "invalid_reason",
            )
        }),
    )

    search_fields = [
        "folio_petition", "agency__acronym", "agency__name",
        "agency__state__short_name"]
    raw_id_fields = ["month_records"]
    inlines = [ComplaintInline]
    list_filter = ["agency"]


class PetitionFileControlAdmin(admin.ModelAdmin):
    from respond.admin import DataFileInline
    list_display = [
        "petition",
        "file_control",
    ]
    list_filter = ["petition__agency"]
    raw_id_fields = ["petition", "file_control"]
    inlines = [DataFileInline]


class VariableInline(admin.StackedInline):
    model = Variable
    extra = 0


class RequestTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "version_name",
        "provider",
        "description",
    ]
    inlines = [VariableInline]
    search_fields = ["provider__acronym", "provider__state__short_name"]
    raw_id_fields = ["provider"]


ocamis_admin_site.register(Petition, PetitionAdmin)
ocamis_admin_site.register(PetitionFileControl, PetitionFileControlAdmin)

ocamis_admin_site.register(MonthRecord, MonthRecordAdmin)
ocamis_admin_site.register(WeekRecord, WeekRecordAdmin)
ocamis_admin_site.register(RequestTemplate, RequestTemplateAdmin)
