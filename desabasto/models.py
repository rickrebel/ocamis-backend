# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import validate_email
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class State(models.Model):
    inegi_code = models.CharField(max_length=2, verbose_name=u"Clave INEGI")
    name = models.CharField(max_length=50, verbose_name=u"Nombre")
    short_name = models.CharField(
        max_length=20, verbose_name=u"Nombre Corto", blank=True, null=True)
    code_name = models.CharField(
        max_length=6, verbose_name=u"Nombre Clave", blank=True, null=True)
    other_names = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.short_name or self.code_name or self.name

    class Meta:
        verbose_name = u"Estado"
        verbose_name_plural = u"Estados"


@python_2_unicode_compatible
class Institution(models.Model):
    name = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE LA INSTITUCION")
    code = models.CharField(
        max_length=20, verbose_name=u"CLAVE DE LA INSTITUCION")
    public_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"NOMBRE PUBLICO DE LA INSTITUCION")
    public_code = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name=u"CLAVE PUBLICA DE LA INSTITUCION")
    relevance = models.IntegerField(
        default=2, verbose_name=u"Relevancia (Para filtros)")

    def __str__(self):
        return self.public_name or self.name


@python_2_unicode_compatible
class CLUES(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE LA UNIDAD")
    is_searchable = models.BooleanField(
        default=False, verbose_name=u"Activo",
        help_text="Puede buscarse por el usuario")
    municipality = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DEL MUNICIPIO")
    municipality_inegi_code = models.CharField(
        max_length=3, verbose_name=u"CLAVE DEL MUNICIPIO")
    tipology = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE TIPOLOGIA")
    tipology_cve = models.CharField(
        max_length=12, verbose_name=u"CLAVE DE TIPOLOGIA")
    id_clues = models.CharField(max_length=10, verbose_name=u"ID_CLUES")
    clues = models.CharField(max_length=20, verbose_name=u"CLUES")
    status_operation = models.CharField(
        max_length=80, verbose_name=u"ESTATUS DE OPERACION")
    longitude = models.CharField(max_length=20, verbose_name=u"LONGITUD")
    latitude = models.CharField(max_length=20, verbose_name=u"LATITUD")
    locality = models.CharField(
        max_length=80, verbose_name=u"NOMBRE DE LA LOCALIDAD")
    locality_inegi_code = models.CharField(
        max_length=5, verbose_name=u"CLAVE DE LA LOCALIDAD")
    jurisdiction = models.CharField(
        max_length=80, verbose_name=u"NOMBRE DE LA JURISDICCION")
    jurisdiction_clave = models.CharField(
        max_length=5, verbose_name=u"CLAVE DE LA JURISDICCION")
    establishment_type = models.CharField(
        max_length=80, verbose_name=u"NOMBRE TIPO ESTABLECIMIENTO")
    consultings_general = models.IntegerField(
        verbose_name=u"CONSULTORIOS DE MED GRAL")
    consultings_other = models.IntegerField(
        verbose_name=u"CONSULTORIOS EN OTRAS AREAS")
    beds_hopital = models.IntegerField(
        verbose_name=u"CAMAS EN AREA DE HOS")
    beds_other = models.IntegerField(
        verbose_name=u"CAMAS EN OTRAS AREAS")
    total_unities = models.IntegerField(
        verbose_name=u"UNIDADES TOTALES (SUMA)")
    admin_institution = models.CharField(
        max_length=80, verbose_name=u"NOMBRE DE LA INS ADM")
    atention_level = models.CharField(
        max_length=80, verbose_name=u"NIVEL ATENCION")
    stratum = models.CharField(
        max_length=80, verbose_name=u"ESTRATO UNIDAD")
    real_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Nombre Limpiado")
    alter_clasifs = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"clasificaciones alternativas")
    clasif_name = models.CharField(
        max_length=120, blank=True, null=True,
        verbose_name=u"Nombre completo tipo")
    prev_clasif_name = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name=u"Nombre corto tipo")
    number_unity = models.CharField(
        max_length=6, verbose_name=u"Número de unidad",
        blank=True, null=True,
    )

    is_national = models.BooleanField(default=False)

    name_in_issten = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE LA UNIDAD",
        blank=True, null=True,
    )

    rr_data = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.clues


@python_2_unicode_compatible
class Responsable(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre")
    emails = models.CharField(
        max_length=255, verbose_name=u"Correos electronicos")
    responsible = models.CharField(
        max_length=255, verbose_name=u"responsible", blank=True, null=True)
    position = models.CharField(
        max_length=255, verbose_name=u"Cargo o posición")
    institution = models.ForeignKey(
        Institution, related_name="responsables",
        blank=True, null=True, on_delete=models.CASCADE)

    state = models.ForeignKey(
        State, blank=True, null=True, related_name="responsables",
        on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, related_name="responsables",
        on_delete=models.CASCADE)

    def __str__(self):
        return u"%s - %s" % (self.name, self.institution)


@python_2_unicode_compatible
class Report(models.Model):
    TYPE = (
        ("paciente", u"Paciente"),
        ("profesional", u"Profesional"),
    )
    medicine_type = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name=u"Tipo de medicina")
    medication_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Nombre de medicamento / Insumo faltante")

    state = models.ForeignKey(
        State, blank=True, null=True, verbose_name=u"Entidad", on_delete=models.CASCADE)
    institution = models.ForeignKey(
        Institution, blank=True, null=True, verbose_name=u"Institución", on_delete=models.CASCADE)
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

    has_corruption = models.NullBooleanField(
        verbose_name=u"¿Incluyó corrupción?")
    narration = models.TextField(
        blank=True, null=True,
        verbose_name=u"Relato de la corrupción")
    informer_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=u"Nombre")
    email = models.CharField(
        max_length=255, validators=[validate_email],
        verbose_name=u"Correo de contacto", blank=True, null=True)
    phone = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"Número de contacto")
    informer_type = models.CharField(
        max_length=20, choices=TYPE,
        verbose_name=u"Tipo de Informante")
    created = models.DateTimeField(
        auto_now_add=True, verbose_name=u"Fecha de Registro")
    origin_app = models.CharField(
        max_length=100, default="CD2",
        verbose_name=u"Aplicacion")
    disease_raw = models.TextField(
        blank=True, null=True, verbose_name=u"Padecimiento")
    validated = models.NullBooleanField(default=None, blank=True, null=True)

    testimony = models.TextField(blank=True, null=True)
    want_litigation = models.NullBooleanField(
        verbose_name=u"¿Permite contacto para litigio?",
        blank=True, null=True)

    validator = models.IntegerField(blank=True, null=True)
    # validator = models.ForeignKey(User, blank=True, null=True)
    validated_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)

    public_testimony = models.NullBooleanField(blank=True, null=True)

    sent_email = models.NullBooleanField(blank=True, null=True)
    sent_responsible = models.NullBooleanField(blank=True, null=True)
    session_ga = models.CharField(max_length=255, blank=True, null=True)

    age = models.IntegerField(
        verbose_name="Edad",
        blank=True, null=True
    )

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

    def save(self, *args, **kwargs):
        is_created = True if self.pk is None else False
        """
        if not self.trimester:
            self.trimester=self.get_trimester
        """

        super(Report, self).save(*args, **kwargs)

        for component in Component.objects.filter(
                supply__report=self).distinct():
            component.update_frecuency()

        if not is_created:
            return
        self.send_informer()

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
        except Exception:
            return
        if not self.email:
            return
        dict_template = self.dict_template()
        dict_template["name"] = self.informer_name
        email_record = EmailRecord()
        email_record.send_email = True
        email_record.email = self.email
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
        verbose_name_plural = u"Reportes"


@python_2_unicode_compatible
class TestimonyMedia(models.Model):
    report = models.ForeignKey(
        Report, related_name=u"testimonies_media", on_delete=models.CASCADE)
    media_file = models.FileField(
        upload_to="cero_desabasto",
        blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "TestimonyMedia"
        verbose_name_plural = "TestimonyMedias"

    def __str__(self):
        if self.media_file:
            return self.media_file.url
        else:
            return self.url


@python_2_unicode_compatible
class Group(models.Model):
    name = models.CharField(max_length=255)
    number = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name.strip() or str(self.number)

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"


@python_2_unicode_compatible
class Component(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(
        max_length=255,
        verbose_name=u"Nombres alternativos y comerciales",
        blank=True, null=True)
    presentation_count = models.IntegerField(default=1)
    frequency = models.IntegerField(default=0, blank=True, null=True)

    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)
    presentations_raw = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)
    is_relevant = models.BooleanField(default=True)

    is_vaccine = models.BooleanField(default=False)

    @property
    def len_short_name(self):
        if not self.short_name:
            return 0
        return len(self.short_name)

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = self.name
        super(Component, self).save(*args, **kwargs)

    def update_frecuency(self):
        self.frequency = Supply.objects\
            .filter(component=self).distinct().count()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Component"
        verbose_name_plural = "Components"


@python_2_unicode_compatible
class PresentationType(models.Model):
    name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    presentation_count = models.IntegerField(default=0)
    agrupated_in = models.ForeignKey(
        "PresentationType", blank=True, null=True, on_delete=models.CASCADE)

    origen_cvmei = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(PresentationType, self).save(*args, **kwargs)

        if self.agrupated_in:
            Presentation.objects.filter(presentation_type=self)\
                .update(presentation_type=self.agrupated_in)

            self.delete()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "PresentationType"
        verbose_name_plural = "PresentationTypes"
        ordering = ["name"]


@python_2_unicode_compatible
class Presentation(models.Model):
    component = models.ForeignKey(
        Component, related_name=u"presentations", on_delete=models.CASCADE)
    presentation_type = models.ForeignKey(
        PresentationType, blank=True, null=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    presentation_type_raw = models.CharField(
        max_length=255, blank=True, null=True)

    clave = models.CharField(max_length=20, blank=True, null=True)
    official_name = models.TextField(blank=True, null=True)
    official_attributes = models.TextField(blank=True, null=True)
    short_attributes = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)

    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return u" ".join([self.component.name, self.short_attributes or ""])

    class Meta:
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"


@python_2_unicode_compatible
class Container(models.Model):
    presentation = models.ForeignKey(
        Presentation, related_name=u"containers", blank=True, null=True, on_delete=models.CASCADE)
    name = models.TextField()
    key = models.CharField(verbose_name=u"Clave", max_length=20)
    key2 = models.CharField(
        max_length=20, verbose_name=u"Clave sin puntos",
        blank=True, null=True,
    )
    is_current = models.NullBooleanField(default=True)
    short_name = models.TextField(blank=True, null=True)

    origen_cvmei = models.NullBooleanField(default=False)

    def __str__(self):
        return u"%s - %s - %s" % (
            self.presentation.component.name,
            self.presentation.presentation_type_raw,
            self.name)

    def save(self, *args, **kwargs):
        if self.key:
            self.key2 = self.key.replace(".", "")
        super(Container, self).save(*args, **kwargs)
        if self.key[:4] == "020.":
            Component.objects.filter(presentations=self.presentation)\
                .update(is_vaccine=True)

    class Meta:
        verbose_name = "Container"
        verbose_name_plural = "Containers"


@python_2_unicode_compatible
class Supply(models.Model):
    MEDICINE_TYPE = (
        ("medicamento", u"Medicamento"),
        ("vacuna", u"Vacuna"),
        ("material", u"Material de curación"),
        ("otro", u"Otro"),
    )

    report = models.ForeignKey(
        Report, related_name="supplies", on_delete=models.CASCADE)
    component = models.ForeignKey(
        Component, blank=True, null=True, on_delete=models.CASCADE)
    # container = models.ForeignKey(Container, blank=True, null=True, on_delete=models.CASCADE)
    presentation = models.ForeignKey(
        Presentation, blank=True, null=True, on_delete=models.CASCADE)

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
        'Disease', blank=True, null=True, verbose_name="Padecimiento", on_delete=models.CASCADE)

    def __str__(self):
        return u"%s - %s" % (
            self.component or self.medicine_real_name or
            self.medicine_name_raw, self.medicine_type)

    class Meta:
        verbose_name = u"Suministro Medico"
        verbose_name_plural = u"Suministros Medicos"


@python_2_unicode_compatible
class Alliances(models.Model):
    name = models.CharField(max_length=180)
    page_url = models.CharField(max_length=180, blank=True, null=True)
    logo = models.FileField()
    level = models.IntegerField(default=2)

    class Meta:
        verbose_name = "Alliances"
        verbose_name_plural = "Alliances"

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "DocumentType"
        verbose_name_plural = "DocumentTypes"

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Disease(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Padecimiento"
        verbose_name_plural = "Padecimientos"

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "MedicalSpeciality"
        verbose_name_plural = "MedicalSpecialitys"

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Medic(models.Model):
    clave_medico = models.CharField(primary_key=True, max_length=30)
    nombre_medico = models.CharField(max_length=255)
    especialidad_medico = models.ForeignKey(
        MedicalSpeciality, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Medic"
        verbose_name_plural = "Medics"

    def __str__(self):
        return str(self.clave_medico)


@python_2_unicode_compatible
class RecipeReport(models.Model):
    year_month = models.IntegerField(blank=True, null=True)
    # clues = models.ForeignKey(CLUES, blank=True, null=True)

    calculate_id = models.IntegerField(blank=True, null=True)
    delegacion = models.CharField(max_length=70, blank=True, null=True)
    clave_presupuestal = models.CharField(max_length=20, blank=True, null=True)
    unidad_medica = models.CharField(max_length=80, blank=True, null=True)
    tipo_unidad_med = models.CharField(max_length=15, blank=True, null=True)
    nivel_atencion = models.IntegerField(blank=True, null=True)
    tipo_documento = models.CharField(max_length=50, blank=True, null=True)
    folio_documento = models.CharField(max_length=50, blank=True, null=True)

    clave_medico = models.CharField(max_length=20, blank=True, null=True)
    nombre_medico = models.CharField(max_length=70, blank=True, null=True)
    especialidad_medico = models.CharField(
        max_length=90, blank=True, null=True)

    delivered = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        verbose_name = "RecipeReport"
        verbose_name_plural = "RecipeReports"

    def __str__(self):
        return self.folio_documento


@python_2_unicode_compatible
class RecipeMedicine(models.Model):
    recipe_id = models.IntegerField(blank=True, null=True)

    fecha_emision = models.DateTimeField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    clave_medicamento = models.CharField(max_length=20, blank=True, null=True)
    cantidad_prescrita = models.IntegerField(blank=True, null=True)
    cantidad_entregada = models.IntegerField(blank=True, null=True)

    precio_medicamento = models.FloatField(blank=True, null=True)
    rn = models.IntegerField(blank=True, null=True)

    delivered = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        verbose_name = "RecipeItem"
        verbose_name_plural = "RecipeItems"

    def __str__(self):
        return str(self.rn)


@python_2_unicode_compatible
class RecipeReport2(models.Model):
    """Nueva vercion del modelo Recipe con atomizado de datos"""
    folio_documento = models.CharField(max_length=40, primary_key=True)
    tipo_documento = models.ForeignKey(DocumentType, on_delete=models.CASCADE)

    delegacion = models.ForeignKey(
        State, blank=True, null=True, on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    medico = models.ForeignKey(
        Medic, blank=True, null=True, on_delete=models.CASCADE)

    year_month = models.IntegerField(blank=True, null=True)
    clave_presupuestal = models.CharField(max_length=20, blank=True, null=True)
    nivel_atencion = models.IntegerField(blank=True, null=True)
    delivered = models.CharField(max_length=3, blank=True, null=True)

    anomaly = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "RecipeReport2"
        verbose_name_plural = "RecipeReports2"

    def __str__(self):
        return self.folio_documento


@python_2_unicode_compatible
class RecipeMedicine2(models.Model):
    recipe = models.ForeignKey(RecipeReport2, on_delete=models.CASCADE)

    fecha_emision = models.DateTimeField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    clave_medicamento = models.CharField(max_length=20, blank=True, null=True)
    cantidad_prescrita = models.IntegerField(blank=True, null=True)
    cantidad_entregada = models.IntegerField(blank=True, null=True)

    precio_medicamento = models.FloatField(blank=True, null=True)
    rn = models.IntegerField(blank=True, null=True)

    delivered = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        verbose_name = "RecipeItem"
        verbose_name_plural = "RecipeItems"

    def __str__(self):
        return str(self.rn)


@python_2_unicode_compatible
class RecipeReportLog(models.Model):
    file_name = models.TextField()
    processing_date = models.DateTimeField(auto_now=True)
    errors = models.TextField(blank=True, null=True)
    successful = models.BooleanField(default=True)

    def get_errors(self):
        import json
        try:
            return json.loads(self.errors)
        except Exception:
            return []

    def set_errors(self, errors_data):
        import json
        try:
            self.errors = json.dumps(errors_data)
        except Exception:
            self.errors = None

    class Meta:
        verbose_name = "RecipeReportLog"
        verbose_name_plural = "RecipeReportLogs"

    def __str__(self):
        return self.folio_documento


# @python_2_unicode_compatible
class PurchaseRaw(models.Model):
    raw_pdf = models.TextField(blank=True, null=True)
    orden = models.CharField(
        max_length=30, blank=True, null=True)
    contrato = models.CharField(
        max_length=70, blank=True, null=True)
    procedimiento = models.CharField(
        max_length=30, blank=True, null=True)
    partida_presupuestal = models.CharField(
        max_length=50, blank=True, null=True)
    rfc = models.CharField(
        max_length=15, blank=True, null=True)
    preveedor = models.TextField(blank=True, null=True)
    expedition_date = models.CharField(
        max_length=10, blank=True, null=True)
    deliver_date = models.CharField(
        max_length=10, blank=True, null=True)
    warehouse = models.TextField(blank=True, null=True)
    adress_warehouse = models.TextField(blank=True, null=True)
    item = models.IntegerField(blank=True, null=True)
    clave_insumo = models.CharField(
        max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    clues = models.TextField(blank=True, null=True)
    entidad = models.CharField(
        max_length=80, blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = u"Orden de Suministro"
        verbose_name_plural = u"Ordenes de Suministro"

    def __unicode__(self):
        return self.orden or 'none'
