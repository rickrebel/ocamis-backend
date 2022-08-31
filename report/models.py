# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import validate_email
from django.db import models
from catalog.models import Institution, State, CLUES, Municipality, Disease
from medicine.models import Component, Presentation
from django.contrib.postgres.fields import JSONField


class Responsable(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre")
    emails = models.CharField(
        max_length=255, verbose_name=u"Correos electronicos",
        help_text="Pueden agregarse varios, separar por comas")
    #responsible = models.CharField(
    #    max_length=255, verbose_name=u"responsible", blank=True, null=True)
    position = models.CharField(
        max_length=255, verbose_name=u"Cargo o posición")
    institution = models.ForeignKey(
        Institution, related_name="responsables", verbose_name="Institución",
        blank=True, null=True, on_delete=models.CASCADE)
    #institution = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey(
        State, blank=True, null=True, related_name="responsables",
        on_delete=models.CASCADE, verbose_name="Entidad")
    #state = models.IntegerField(blank=True, null=True)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, related_name="responsables",
        on_delete=models.CASCADE, verbose_name="Clínica u Hospital")
    update_date = models.DateField(
        null=True, blank=True, verbose_name="Fecha de actualización")
    petition_date = models.DateField(
        null=True, blank=True, verbose_name="Fecha respuesta oficio")
    notes = models.TextField(
        verbose_name="Notas", null=True, blank=True)
    #clues = models.IntegerField(blank=True, null=True)
    is_covid = models.BooleanField(
        default=False, verbose_name=u"Responsable COVID")

    def __str__(self):
        return u"%s - %s" % (self.name, self.institution)

    class Meta:
        verbose_name = u"Responsable"
        verbose_name_plural = u"6. Responsables"
        db_table = u'desabasto_responsable'


class Persona(models.Model):

    informer_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=u"Nombre")
    email = models.CharField(
        max_length=255, validators=[validate_email],
        verbose_name=u"Correo de contacto", blank=True, null=True)
    phone = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Número de contacto")
    want_litigation = models.NullBooleanField(
        verbose_name=u"¿Permite contacto para asesoría legal?",
        blank=True, null=True)
    want_management = models.NullBooleanField(
        verbose_name=u"¿Permite contacto para acompañar proceso?",
        blank=True, null=True)

    class Meta:
        verbose_name = u"Persona Reportante"
        verbose_name_plural = u"4. Personas Reportantes"

    def __str__(self):
        return "%s - %s" % (
            self.informer_name or "sin datos", self.email or '--')


class Report(models.Model):
    TYPE = (
        ("paciente", u"Paciente"),
        ("profesional", u"Profesional"),
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name=u"Fecha de Registro")
    persona = models.ForeignKey(
        Persona, blank=True, null=True, verbose_name=u"Persona reportante",
        on_delete=models.CASCADE)
    state = models.ForeignKey(
        State, blank=True, null=True, verbose_name=u"Entidad",
        on_delete=models.CASCADE)
    institution = models.ForeignKey(
        Institution, blank=True, null=True, verbose_name=u"Institución",
        on_delete=models.CASCADE)
    institution_raw = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Institución escrita")
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    is_other = models.BooleanField(
        default=False, verbose_name=u"Es otra institución")
    hospital_name_raw = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Nombre de hospital o clínica")
    disease_raw = models.TextField(
        blank=True, null=True, verbose_name=u"Padecimiento")
    age = models.IntegerField(
        verbose_name="Edad",
        blank=True, null=True
    )

    informer_type = models.CharField(
        max_length=20, choices=TYPE,
        verbose_name=u"Tipo de Informante")

    #Va a Persona:
    informer_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=u"Nombre")
    email = models.CharField(
        max_length=255, validators=[validate_email],
        verbose_name=u"Correo de contacto", blank=True, null=True)
    phone = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Número de contacto")
    want_litigation = models.NullBooleanField(
        verbose_name=u"¿Permite contacto para litigio?",
        blank=True, null=True)

    #Va a ComplementReport:
    origin_app = models.CharField(
        max_length=100, default="CD2",
        verbose_name=u"Aplicacion")
    validated = models.NullBooleanField(default=None, blank=True, null=True)
    session_ga = models.CharField(max_length=255, blank=True, null=True)
    validator = models.IntegerField(blank=True, null=True)
    validated_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)

    testimony = models.TextField(blank=True, null=True)
    public_testimony = models.NullBooleanField(blank=True, null=True)
    has_corruption = models.NullBooleanField(
        verbose_name=u"¿Incluyó corrupción?")
    narration = models.TextField(
        blank=True, null=True,
        verbose_name=u"Relato de la corrupción")

    #DEBERÍAN ELIMINARSE:
    sent_email = models.NullBooleanField(blank=True, null=True)
    sent_responsible = models.NullBooleanField(blank=True, null=True)
    medicine_type = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name=u"Tipo de medicina")
    medication_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Nombre de medicamento / Insumo faltante")

    @property
    def get_medicine_type(self):
        return self.get_medicine_type_display()

    @property
    def get_informer_type(self):
        return self.get_informer_type_display()

    @property
    def get_clues_hospital_name(self):
        if self.clues:
            return self.clues.name
        else:
            return self.hospital_name_raw

    @property
    def get_institution_name(self):
        if self.clues:
            return self.clues.institution.public_name
        elif self.institution:
            return self.institution.public_name
        else:
            return self.institution_raw

    def get_trimester(self):
        from scripts.common import get_datetime_mx
        from django.utils import timezone
        if not hasattr(self, "_trimester"):
            mx_datetime = get_datetime_mx(self.created or timezone.now())
            self._trimester = int(mx_datetime.month / 3) + \
                (1 if mx_datetime.month % 3 else 0)

    @property
    def trimester(self):
        return self.get_trimester()

    def update_trimester(self):
        return
        Report.objects.filter(id=self.id)\
            .update(trimester=self.get_trimester())

    """def save(self, *args, **kwargs):
        is_created = True if self.pk is None else False

        super(Report, self).save(*args, **kwargs)

        for component in Component.objects.filter(
                supply__report=self).distinct():
            component.update_frecuency()

        if not is_created:
            return
        self.send_informer()"""

    def dict_template(self, simple=True):
        # Variables para templates--------------------------------------------
        institution_obj = self.institution or getattr(
            self.clues, "institution", None)
        institution_name = (getattr(institution_obj, "name", None) or
                            self.institution_raw or u"No identificado")

        state_obj = self.state or getattr(self.clues, "state", None)
        state_name = (getattr(state_obj, "short_name", None) or
                      u"No identificado")
        if simple:
            return {
                "institution": institution_name,
                "state": state_name
            }

        hospital_name = (getattr(self.clues, "name", None) or
                         self.hospital_name_raw or u'No identificado')
        clues_code = getattr(self.clues, "clues", None) or 'No identificado'

        supplies_list = []
        for supply in Supply.objects.filter(report=self):
            supply_str = ""
            if supply.component:
                supply_str = supply.component.name + " " + (
                    getattr(supply.presentation, "description", None) or
                    supply.presentation_raw or ""
                )
            else:
                supply_str = (supply.medicine_name_raw or "") + " " + (
                    supply.presentation_raw or "")
            if not supply_str.strip():
                continue
            supplies_list.append(supply_str.strip())
        supplies = u", ".join(supplies_list)
        return {
            "institution": institution_name,
            "state": state_name,
            "hospital": hospital_name,
            "clues": clues_code,
            "supplies": supplies,
            "id": self.id,
            "created": self.created.strftime("%d/%m/%Y"),
        }
        # Variables para templates--------------------------------------------

    def send_informer(self):
        from email_sendgrid.models import (TemplateBase, EmailRecord,
                                           SendGridProfile)
        sendgrid_nosotrxs = SendGridProfile.objects\
            .filter(name="Nosotrxs").first()
        try:
            template_informer = TemplateBase.objects\
                .get(name="template_informer")
        except Exception as e:
            print(e)
            return
        if not self.persona:
            return
        elif not self.persona.email:
            return
        dict_template = self.dict_template()
        dict_template["name"] = self.persona.informer_name
        email_record = EmailRecord()
        email_record.send_email = True
        email_record.email = self.persona.email
        email_record.sendgrid_profile = sendgrid_nosotrxs
        email_record.template_base = template_informer
        email_record.type_message = "Cero Desabasto Informante"

        email_record.save(user_data=dict_template)

    def send_responsable(self):
        from django.db.models import Q
        from email_sendgrid.models import (TemplateBase, EmailRecord,
                                           SendGridProfile)
        sendgrid_nosotrxs = SendGridProfile.objects\
            .filter(name="Nosotrxs").first()
        try:
            template_responsable = TemplateBase.objects\
                .get(name="template_responsable")
        except Exception:
            return

        if self.clues:
            institution = self.clues.institution
            state = self.clues.state if not self.clues.is_national else None
        else:
            institution = self.institution
            state = self.state

        responsables = Responsable.objects\
            .filter(
                Q(
                    clues=self.clues, clues__isnull=False) |
                Q(
                    clues__isnull=True,
                    state=state, state__isnull=False,
                    institution=institution, institution__isnull=False) |
                Q(
                    institution=institution, institution__isnull=False,
                    state__isnull=True,
                    clues__isnull=True)
            ).distinct()

        dict_template = self.dict_template(simple=False)
        for responsable in responsables:
            emails = responsable.emails
            emails = [email.strip() for email in emails.split(",")]
            dict_template["responsible_name"] = responsable.name
            # print responsable
            # print responsable.clues
            # print responsable.state
            # print responsable.institution
            # print emails
            # print
            # continue
            for responsable_email in emails:
                email_record = EmailRecord()
                email_record.send_email = True
                email_record.email = responsable_email
                email_record.sendgrid_profile = sendgrid_nosotrxs
                email_record.template_base = template_responsable
                email_record.type_message = "Cero Desabasto Responsable"
                email_record.save(user_data=dict_template)

    def __str__(self):
        return u"%s - %s -- %s" % (self.state, self.institution, self.created)

    class Meta:
        verbose_name = u"Reporte"
        verbose_name_plural = u"1. Reportes"
        db_table = u'desabasto_report'


class CovidReport(models.Model):
    created = models.DateTimeField(
        auto_now_add=True, verbose_name=u"Fecha de Registro")
    persona = models.ForeignKey(
        Persona, blank=True, null=True, verbose_name=u"Persona reportante",
        on_delete=models.CASCADE)
    state = models.ForeignKey(
        State, blank=True, null=True, verbose_name=u"Entidad",
        on_delete=models.CASCADE)
    municipality = models.ForeignKey(
        Municipality, blank=True, null=True,
        verbose_name=u"Municipio residencia",
        on_delete=models.CASCADE)
    other_location = models.CharField(max_length=255, null=True, blank=True)
    age = models.IntegerField(verbose_name="Edad", blank=True, null=True)
    gender = models.CharField(
        max_length=40, verbose_name="Género", blank=True, null=True)
    special_group = models.CharField(
        max_length=80, verbose_name="Grupo especial", blank=True, null=True)
    comorbilities = JSONField(
        verbose_name="Comorbilidades", blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.state, self.created)

    class Meta:
        verbose_name = u"Reporte COVID"
        verbose_name_plural = u"3. Reportes COVID"


class DosisCovid(models.Model):
    covid_report = models.ForeignKey(
        CovidReport, blank=True, null=True,
        verbose_name=u"Reporte Covid", related_name="dosis",
        on_delete=models.CASCADE)
    is_success = models.BooleanField(
        default=False, verbose_name="Es dosis aplicada")
    state = models.ForeignKey(
        State, blank=True, null=True, verbose_name=u"Entidad",
        on_delete=models.CASCADE)
    municipality = models.ForeignKey(
        Municipality, blank=True, null=True, verbose_name=u"Municipio",
        on_delete=models.CASCADE)
    other_location = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    round_dosis = models.CharField(
        max_length=60, blank=True, null=True, verbose_name=u"Número de dosis")
    date = models.DateField(blank=True, null=True, verbose_name=u"Fecha")
    reason_negative = models.TextField(
        blank=True, null=True, verbose_name=u"Razón de negativa")

    @property
    def get_type_success(self):
        return "Sí aplicada" if self.is_success else "No aplicada"

    def __str__(self):
        return u"%s (%s) - %s" % (
            self.brand or '?', self.round_dosis or '?',
            u'aplicada' if self.is_success else u'negada')

    class Meta:
        verbose_name = u"Dosis"
        verbose_name_plural = u"5. Dosis aplicadas y negadas"


class ComplementReport(models.Model):
    report = models.OneToOneField(
        Report, blank=True, null=True, related_name="complement",
        on_delete=models.CASCADE)
    covid_report = models.OneToOneField(
        CovidReport, blank=True, null=True, related_name="complement",
        on_delete=models.CASCADE)
    key = models.CharField(max_length=30, default='')

    testimony = models.TextField(blank=True, null=True)
    public_testimony = models.NullBooleanField(blank=True, null=True)
    has_corruption = models.NullBooleanField(
        verbose_name=u"¿Incluyó corrupción?")
    narration = models.TextField(
        blank=True, null=True,
        verbose_name=u"Relato de la corrupción")
    notes = models.TextField(
        blank=True, null=True,
        verbose_name=u"Notas (para corrección)")

    validated = models.NullBooleanField(default=None, blank=True, null=True)
    validator = models.IntegerField(blank=True, null=True)
    validated_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)

    session_ga = models.CharField(max_length=255, blank=True, null=True)
    origin_app = models.CharField(
        max_length=100, default="CD2",
        verbose_name=u"Aplicación")

    def save(self, *args, **kwargs):
        import random
        import string
        print(self)
        if not self.pk:
            self.key = ''.join([
                random.choice(string.ascii_letters + string.digits)
                for n in range(30)])
        else:
            self.key = ''
        super(ComplementReport, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.report or self.covid_report

    class Meta:
        verbose_name = u"Complemento de un reporte"
        verbose_name_plural = u"Complementos de reportes"


class TestimonyMedia(models.Model):
    report = models.ForeignKey(
        Report, related_name=u"testimonies_media", on_delete=models.CASCADE)
    #report = models.IntegerField()
    media_file = models.FileField(
        upload_to="cero_desabasto",
        blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = u"Archivo de testimonio"
        verbose_name_plural = u"8. Archivos de testimonio"
        db_table = u'desabasto_testimonymedia'

    def __str__(self):
        if self.media_file:
            return self.media_file.url
        else:
            return self.url


class Supply(models.Model):
    MEDICINE_TYPE = (
        ("medicamento", u"Medicamento"),
        ("vacuna", u"Vacuna"),
        ("material", u"Material de curación"),
        ("otro", u"Otro"),
    )

    report = models.ForeignKey(
        Report, related_name="supplies", on_delete=models.CASCADE)
    #report = models.IntegerField()
    component = models.ForeignKey(
        Component, blank=True, null=True, on_delete=models.CASCADE)
    #component = models.IntegerField(blank=True, null=True)
    # container = models.ForeignKey(Container, blank=True, null=True)
    presentation = models.ForeignKey(
        Presentation, blank=True, null=True, on_delete=models.CASCADE)
    #presentation = models.IntegerField(blank=True, null=True)

    medicine_type = models.CharField(
        max_length=20, verbose_name=u"Tipo de Medicamento",
        blank=True, null=True,
    )
    medicine_name_raw = models.CharField(
        max_length=255, verbose_name=u"Nombre reportado del medicamento",
        blank=True, null=True,
    )

    presentation_raw = models.CharField(max_length=255, blank=True, null=True)
    medicine_real_name = models.CharField(
        max_length=255, verbose_name=u"Nombre real del medicamento",
        blank=True, null=True,
    )
    disease = models.ForeignKey(
        Disease, blank=True, null=True, verbose_name="Padecimiento",
        on_delete=models.CASCADE)
    #disease = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (
            self.component or self.medicine_real_name or
            self.medicine_name_raw, self.medicine_type)

    class Meta:
        verbose_name = u"Medicamento o insumo"
        verbose_name_plural = u"2. Medicamentos/Insumos de reportes"
        db_table = u'desabasto_supply'
