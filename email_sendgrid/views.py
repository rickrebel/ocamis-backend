# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http.response import HttpResponse
from django.views import generic
from django.conf import settings as dj_settings

import json


class SendGridWebhook(generic.View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Hola")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from email_sendgrid.models import EmailRecord, EmailEventHistory
        # webhook_slug = kwargs.get("webhook_slug")
        incoming_events = json.loads(self.request.body.decode("utf-8"))
        for event_data in incoming_events:
            sg_message_id = event_data.get("sg_message_id")
            email = event_data.get("email")
            event = event_data.get("event")
            if not sg_message_id:
                continue

            email_record = EmailRecord.objects.filter(
                sg_message_id=sg_message_id).first()
            if not email_record:
                try:
                    x_message_id = sg_message_id.split(".")[0]
                except Exception as e:
                    print(e)
                    continue
                try:
                    email_record = EmailRecord.objects.get(
                        x_message_id=x_message_id,
                        email=email)
                except Exception as e:
                    print(e)
                    email_record = EmailRecord()
                    email_record.email = email
                    email_record.x_message_id = x_message_id
                    email_record.sg_message_id = sg_message_id
                    super(EmailRecord, email_record).save()

            EmailRecord.objects.filter(id=email_record.id)\
                .update(sg_message_id=sg_message_id)
            email_record.sg_message_id = sg_message_id

            EmailEventHistory.objects.create(
                event=event,
                event_data=event_data,
                email_record=email_record
            )

        return HttpResponse()


def send_email(from_email, email, subject, html_content, all_obj=False):

    import requests
    sendgrid_api_key = getattr(dj_settings, "SENDGRID_API_KEY", None)
    if not sendgrid_api_key:
        print("no esta configurado SENDGRID_API_KEY")
        return

    headers = {
        'Authorization': "Bearer %s" % sendgrid_api_key,
        'Content-Type': 'application/json',
    }
    data = {
        "personalizations": [{
            "to": [{"email": email}],
            "subject": subject
        }],
        "from": {
            "email": "info@yeeko.org",
            "name": from_email
        },
        "content": [{
            "type": "text/html",
            "value": html_content
        }]
    }

    response = requests.post('https://api.sendgrid.com/v3/mail/send',
                             headers=headers, data=json.dumps(data))
    if all_obj:
        return response
    elif response.status_code == 202:
        return response.headers.get("X-Message-Id")
    else:
        return False
