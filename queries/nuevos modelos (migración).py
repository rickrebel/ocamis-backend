# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from report.models import Report, Persona, ComplementReport



Persona.objects.all().delete()
ComplementReport.objects.all().delete()

all_reports = Report.objects.all()
for rp in all_reports:
    persona = Persona.objects.create(
        email=rp.email,
        informer_name=rp.informer_name,
        phone=rp.phone)
    rp.persona = persona
    rp.save()
    complement = ComplementReport.objects.create(
        report=rp,
        testimony=rp.testimony,
        public_testimony=rp.public_testimony,
        has_corruption=rp.has_corruption,
        narration=rp.narration,
        validated=rp.validated,
        validator=rp.validator,
        validated_date=rp.validated_date,
        pending=rp.pending,
        session_ga=rp.session_ga,
        origin_app=rp.origin_app)






