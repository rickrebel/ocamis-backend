# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.conf import settings


class SendGridProfile(models.Model):
    name = models.CharField(max_length=200, unique=True)
    sendgrid_api_key = models.CharField(max_length=255)
    webhook_slug = models.CharField(max_length=255, blank=True, null=True)
    from_email = models.CharField(max_length=100)
    default = models.BooleanField(default=False)
    test_mode = models.BooleanField(default=False)
    test_emails = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.default:
            SendGridProfile.objects.all().update(default=False)
        super(SendGridProfile, self).save(*args, **kwargs)

    def send_email(self, from_name, to_email, subject, html_content):
        import requests
        import json
        from django.core.validators import validate_email
        headers = {
            'Authorization': "Bearer %s" % self.sendgrid_api_key,
            'Content-Type': 'application/json',
        }
        data = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "subject": subject
            }],
            "from": {
                "email": self.from_email,
                "name": from_name or self.from_email
            },
            "content": [{
                "type": "text/html",
                "value": html_content
            }]
        }
        if self.test_mode:
            test_to = []
            for email in self.test_emails.split(","):
                email = email.lower().strip()
                try:
                    validate_email(email)
                except Exception:
                    continue
                test_to.append({"email": email})
            data["personalizations"][0]["to"] = test_to

        response = requests.post('https://api.sendgrid.com/v3/mail/send',
                                 headers=headers, data=json.dumps(data))
        if response.status_code == 202:
            return response.headers.get("X-Message-Id")
        else:
            return False

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Perfil de correo por SendGrid"
        verbose_name_plural = "Perfiles de correo por SendGrid"


class TemplateBase(models.Model):
    subject = models.CharField(max_length=200)
    from_name = models.CharField(max_length=200)
    name = models.CharField(max_length=200, null=True)
    body = RichTextField()
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    sendgrid_profile = models.ForeignKey(
        SendGridProfile, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.from_name + ": " + self.subject

    class Meta:
        verbose_name = "Plantilla Base"
        verbose_name_plural = "Plantillas Base"
        db_table = u'perfil_templatebase'


class MassMailing(models.Model):
    template_base = models.ForeignKey(
        TemplateBase, blank=True, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    filter_kwargs = models.TextField(blank=True, null=True)
    exclude_kwargs = models.TextField(blank=True, null=True)
    order_by_args = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.created, self.template_base)

    class Meta:
        db_table = u'perfil_massmailing'


def email_body_tags(user, body):
    from django.template import Context, Template
    reemplazos_dict = {}
    if isinstance(user, User):
        reemplazos_dict["name"] = " ".join([user.first_name,
                                            user.last_name or ""])
        reemplazos_dict["email"] = user.email or ""
        reemplazos_dict["username"] = user.username or ""
    elif isinstance(user, dict):
        for key, value in user.items():
            reemplazos_dict[key] = "%s" % (value or "")

    template = Template(body)
    context = Context(reemplazos_dict)
    return template.render(context)


class EmailRecord(models.Model):
    send_email = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE)
    email = models.CharField(max_length=120, blank=True, null=True)
    sendgrid_profile = models.ForeignKey(
        SendGridProfile, blank=True, null=True, on_delete=models.CASCADE)
    template_base = models.ForeignKey(
        TemplateBase, blank=True, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    x_message_id = models.CharField(max_length=120, blank=True, null=True)
    sg_message_id = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, default="unknown")
    status_date = models.DateTimeField(blank=True, null=True)
    type_message = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        from email_sendgrid.views import send_email
        is_created = True if self.pk is None else False
        user_data = kwargs.pop("user_data", None)
        type_message = kwargs.pop("type_message", None)
        if self.template_base and not self.sendgrid_profile:
            self.sendgrid_profile = self.template_base.sendgrid_profile
        if not self.sendgrid_profile:
            self.sendgrid_profile = SendGridProfile.objects\
                .filter(default=True).first()
        super(EmailRecord, self).save(*args, **kwargs)
        if is_created and self.send_email:
            if self.template_base:
                subject = self.template_base.subject
                from_name = self.template_base.from_name
                body = self.template_base.body
            else:
                subject = getattr(settings, "EMAIL_SUBJECT", "email yeeko")
                from_name = getattr(settings, "EMAIL_FROM", "Yeeko")
                body = getattr(settings, "EMAIL_BODY", None)
            if not body:
                return
            if user_data:
                body = email_body_tags(user_data, body)
                subject = email_body_tags(user_data, subject)
            elif self.user:
                body = email_body_tags(self.user, body)
                subject = email_body_tags(self.user, subject)
            if not self.email:
                if not self.user.email:
                    return
                self.email = self.user.email
            self.type_message = type_message or self.type_message
            if self.sendgrid_profile:
                self.x_message_id = self.sendgrid_profile.send_email(
                    from_name, self.email, subject, body)
            else:
                self.x_message_id = send_email(
                    from_name, self.email, subject, body)
            # actualizacion de datos tras envio de correo
            super(EmailRecord, self).save()

    def __str__(self):
        return "%s - %s -- %s" % (self.email, self.status, self.created)

    class Meta:
        verbose_name = "Envio de Email"
        verbose_name_plural = "Envios de Emails"
        db_table = u'perfil_emailrecord'


class EmailEventHistory(models.Model):
    event = models.CharField(max_length=20)
    response_date = models.DateTimeField(auto_now_add=True)
    event_data = models.TextField()
    email_record = models.ForeignKey(EmailRecord, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.pk is None:
            is_created = True
        else:
            is_created = False
        super(EmailEventHistory, self).save(*args, **kwargs)
        if is_created:
            EmailRecord.objects.filter(id=self.email_record.id)\
                .update(status=self.event, status_date=self.response_date)

    class Meta:
        db_table = u'perfil_emaileventhistory'
