# -*- coding: UTF-8 -*-
from django.contrib import admin
from email_sendgrid.models import (
    EmailRecord, EmailEventHistory, TemplateBase, SendGridProfile)


class EmailEventHistoryInLine(admin.TabularInline):
    model = EmailEventHistory
    extra = 0


class EmailRecordAdmin(admin.ModelAdmin):
    model = EmailRecord
    raw_id_fields = ["user"]
    list_display = [
        "email", "user", "x_message_id", "status", "created", "type_message"]
    list_filter = ["sendgrid_profile", "type_message", "created"]
    inlines = [EmailEventHistoryInLine]
    readonly_fields = ["created"]


admin.site.register(EmailRecord, EmailRecordAdmin)


class TemplateBaseAdmin(admin.ModelAdmin):
    model = TemplateBase
    fields = [
        "subject",
        "from_name",
        "name",
        "body",
        "description",
        "sendgrid_profile",
        "created",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["created", "name"]
        else:
            return ["created"]


admin.site.register(TemplateBase, TemplateBaseAdmin)

admin.site.register(SendGridProfile)
