# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import JSONField


def default_alternative_names():
    return []


class State(models.Model):
    inegi_code = models.CharField(max_length=2, verbose_name="Clave INEGI")
    name = models.CharField(max_length=50, verbose_name="Nombre")
    short_name = models.CharField(
        max_length=20, verbose_name="Nombre Corto",
        blank=True, null=True)
    code_name = models.CharField(
        max_length=6, verbose_name="Nombre Clave",
        blank=True, null=True)
    other_names = models.CharField(
        verbose_name="Otros nombres",
        help_text="No utilizar para OCAMIS, es solo para para cero desabasto",
        max_length=255, blank=True, null=True)
    alternative_names = JSONField(
        default=default_alternative_names,
        verbose_name="Lista nombres alternativos",
        help_text="Ocupar para OCAMIS",
        )

    def __str__(self):
        return self.short_name or self.code_name or self.name

    class Meta:
        ordering = ["inegi_code"]
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        db_table = u'desabasto_state'


class Municipality(models.Model):
    inegi_code = models.CharField(max_length=6, verbose_name="Clave INEGI")
    name = models.CharField(max_length=120, verbose_name="Nombre")
    state = models.ForeignKey(
        State, verbose_name="Entidad",
        null=True, on_delete=models.CASCADE,
        related_name="municipalities")

    def __str__(self):
        return "%s - %s" % (self.name, self.state)

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"


class Institution(models.Model):
    name = models.CharField(
        max_length=255, verbose_name="NOMBRE DE LA INSTITUCION")
    code = models.CharField(
        max_length=20, verbose_name="CLAVE DE LA INSTITUCION")
    public_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="NOMBRE PUBLICO DE LA INSTITUCION")
    public_code = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="CLAVE PUBLICA DE LA INSTITUCION")
    relevance = models.IntegerField(
        default=2, verbose_name="Relevancia (Para filtros)")

    def __str__(self):
        return self.public_name or self.name

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        db_table = u'desabasto_institution'


class Typology(models.Model):
    clave = models.CharField(
        max_length=50, verbose_name="Clave oficial")
    name = models.CharField(
        max_length=255, verbose_name="Nombre oficial")
    public_name = models.CharField(
        max_length=255, verbose_name="Nombre corto (modificado)",
        blank=True, null=True)
    alternative_names = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s (%s)" % (self.clave, self.name)

    class Meta:
        verbose_name = "Tipología"
        verbose_name_plural = "Tipologías"


class CLUES(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    #state = models.IntegerField()
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE)
    #institution = models.IntegerField()
    name = models.CharField(
        max_length=255, verbose_name="NOMBRE DE LA UNIDAD")
    key_issste = models.CharField(
        max_length=12, verbose_name="CLAVE ISSSTE",
        blank=True, null=True)
    is_searchable = models.BooleanField(
        default=False, verbose_name="Activo",
        help_text="Puede buscarse por el usuario")
    municipality = models.CharField(
        max_length=255, verbose_name="NOMBRE DEL MUNICIPIO")
    municipality_inegi_code = models.ForeignKey(
        Municipality, on_delete=models.CASCADE)
    typology = models.CharField(
        max_length=255, verbose_name="NOMBRE DE TIPOLOGIA")
    typology_obj = models.ForeignKey(
        Typology, verbose_name="Tipología (Catálogo)",
        blank=True, null=True, on_delete=models.CASCADE)
    typology_cve = models.CharField(
        max_length=12, verbose_name="CLAVE DE TIPOLOGÍA")
    id_clues = models.CharField(max_length=10, verbose_name="ID_CLUES")
    clues = models.CharField(max_length=20, verbose_name="CLUES")
    status_operation = models.CharField(
        max_length=80, verbose_name="ESTATUS DE OPERACIÓN")
    longitude = models.CharField(max_length=20, verbose_name="LONGITUD")
    latitude = models.CharField(max_length=20, verbose_name="LATITUD")
    locality = models.CharField(
        max_length=80, verbose_name="NOMBRE DE LA LOCALIDAD")
    locality_inegi_code = models.CharField(
        max_length=5, verbose_name="CLAVE DE LA LOCALIDAD")
    jurisdiction = models.CharField(
        max_length=80, verbose_name="NOMBRE DE LA JURISDICCIÓN")
    jurisdiction_clave = models.CharField(
        max_length=5, verbose_name="CLAVE DE LA JURISDICCIÓN")
    jurisdiction_obj = models.ForeignKey(
        "Jurisdiction", verbose_name="Jurisdicción Sanitaria",
        blank=True, null=True, on_delete=models.CASCADE,
        related_name="jurisdictions")
    establishment_type = models.CharField(
        max_length=80, verbose_name="NOMBRE TIPO ESTABLECIMIENTO")
    consultings_general = models.IntegerField(
        verbose_name="CONSULTORIOS DE MED GRAL")
    consultings_other = models.IntegerField(
        verbose_name="CONSULTORIOS EN OTRAS AREAS")
    beds_hopital = models.IntegerField(
        verbose_name="CAMAS EN AREA DE HOS")
    beds_other = models.IntegerField(
        verbose_name="CAMAS EN OTRAS AREAS")
    total_unities = models.IntegerField(
        verbose_name="UNIDADES TOTALES (SUMA)")
    admin_institution = models.CharField(
        max_length=80, verbose_name="NOMBRE DE LA INS ADM")
    atention_level = models.CharField(
        max_length=80, verbose_name="NIVEL ATENCIÓN")
    stratum = models.CharField(
        max_length=80, verbose_name="ESTRATO UNIDAD")
    real_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Nombre Limpiado")
    alter_clasifs = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="clasificaciones alternativas")
    clasif_name = models.CharField(
        max_length=120, blank=True, null=True,
        verbose_name="Nombre completo tipo")
    prev_clasif_name = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name="Nombre corto tipo")
    number_unity = models.CharField(
        max_length=6, verbose_name="Número de unidad",
        blank=True, null=True,
    )

    is_national = models.BooleanField(default=False)

    name_in_issten = models.CharField(
        max_length=255, verbose_name="NOMBRE DE LA UNIDAD",
        blank=True, null=True,
    )

    rr_data = models.TextField(blank=True, null=True)
    alternative_names = JSONField(blank=True, null=True)
    
    #Nuevos fields
    type_street = models.CharField(
        max_length=80, blank=True, null=True, 
        verbose_name="TIPO DE VIALIDAD")
    street = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="VIALIDAD")    
    streat_number = models.CharField(
        max_length=80, blank=True, null=True, 
        verbose_name="NÚMERO CALLE")
    suburb = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="SUBURBIO")
    postal_code = models.CharField(
        max_length=6, blank=True, null=True,
        verbose_name="CODIGO POSTAL")
    rfc = models.CharField(
        max_length=6, blank=True, null=True,
        verbose_name="RFC")
    last_change = models.DateTimeField(
        blank=True, null=True,
         verbose_name="FECHA ULTIMO MOVIMIENTO")

    def __str__(self):
        return self.clues

    class Meta:
        verbose_name = "Hospital o clínica CLUES"
        verbose_name_plural = "Catálogo CLUES"
        db_table = u'desabasto_clues'


class Delegation(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    institution = models.ForeignKey(
        Institution, verbose_name="Institución",
        on_delete=models.CASCADE)
    state = models.ForeignKey(
        State, verbose_name="Entidad",
        on_delete=models.CASCADE)
    clues = models.OneToOneField(
        CLUES, blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="related_delegation")
    other_names = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s --%s" % (
            self.name, self.state, self.institution)

    class Meta:
        verbose_name = "Delegación"
        verbose_name_plural = "Delegaciones"


class Jurisdiction(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    key = models.CharField(max_length=50, verbose_name="Clave")
    institution = models.ForeignKey(
        Institution, verbose_name="Institución",
        on_delete=models.CASCADE)
    state = models.ForeignKey(
        State, verbose_name="Entidad",
        on_delete=models.CASCADE)

    def __str__(self):
        return "%s -- %s --%s" % (
            self.name, self.state, self.institution)

    class Meta:
        verbose_name = "Jurisdicción"
        verbose_name_plural = "Jurisdicciones"


class Disease(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Padecimiento"
        verbose_name_plural = "7. Padecimientos"
        db_table = u'desabasto_disease'

    def __str__(self):
        return self.name


class Alliances(models.Model):
    name = models.CharField(max_length=180)
    page_url = models.CharField(
        verbose_name="Página web",
        max_length=180, blank=True, null=True)
    logo = models.FileField()
    level = models.IntegerField(default=2)
    diseases_litigation = models.ManyToManyField(
        Disease, related_name="litigations",
        verbose_name="Padecimientos asociados (asesoría legal)",
        blank=True)
    diseases_management = models.ManyToManyField(
        Disease, related_name="managements",
        verbose_name="Padecimientos asociados (acompañamiento)",
        blank=True)
    page_help = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Página web de asistencia")
    email = models.CharField(
        max_length=255, verbose_name="Email para asistencia",
        blank=True, null=True)
    phone = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Número de contacto")

    class Meta:
        verbose_name = "Alianza"
        verbose_name_plural = "Alianzas"
        db_table = u'desabasto_alliances'

    def __str__(self):
        return self.name


class Entity(models.Model):
    name = models.CharField(
        max_length=120, blank=True, null=True,
        verbose_name="Nombre",
        help_text="Solo cuando sea distinta al nombre de la institución/CLUES"
        )
    acronym = models.CharField(
        max_length=20, verbose_name="Siglas del Sujeto Obligado",
        blank=True, null=True)
    idSujetoObligado = models.IntegerField(
        verbose_name="idSujetoObligado",
        help_text="idSujetoObligado del INAI",
        blank=True, null=True)
    nameForInai = models.CharField(
        max_length=255,
        verbose_name="nombre según INAI",
        blank=True, null=True)
    nombreSujetoObligado = models.CharField(
        max_length=160,
        verbose_name="nombreSujetoObligado)",
        help_text="nombreSujetoObligado del INAI",
        blank=True, null=True)
    institution = models.ForeignKey(
        'Institution', on_delete=models.CASCADE)
    state = models.ForeignKey(
        'State',
        null= True, blank=True,
        on_delete=models.CASCADE)
    clues = models.ForeignKey(
        'CLUES', null=True, 
        blank=True, on_delete=models.CASCADE)
    addl_params = JSONField(blank=True, null=True)
    vigencia = models.BooleanField(
        default=True, help_text="Actualmente se le sigue preguntando")
    competent = models.BooleanField(
        default=True,
        verbose_name="Competente",
        help_text="Es Competente porque tiene pacientes y debe tener la información")
    notes = models.TextField(blank=True, null=True)
    is_pilot = models.BooleanField(default=False)
    population = models.IntegerField(
        verbose_name="Derechohabientes", blank=True, null=True)

    def save(self, *args, **kwargs):
        from inai.models import MonthEntity
        self_created = True if self.pk is None else False
        super(Entity, self).save(*args, **kwargs)
        if self_created:
            for sum_year in range(7):
                year = sum_year + 2017
                for month in range(12):
                    month += 1
                    ye_mo = "%s%s%s" % (year, '0' if month < 10 else '', month)
                    MonthEntity.objects.get_or_create(entity=self, year_month=ye_mo)

    def __str__(self):
        return self.name or "%s -%s -%s" % (
            self.institution, self.state, self.clues)

    @property
    def entity_type(self):
        if self.clues:
            return 'Hospital Federal'
        elif self.state:
            return 'Estatal'
        else:
            return 'Nacional'

    class Meta:
        ordering = ["state__name"]
        verbose_name = "Sujeto Obligado"
        verbose_name_plural = "Sujetos Obligados"


class Area(models.Model):

    key = models.CharField(
        max_length=255, verbose_name="Clave del área",
        blank=True, null=True)
    name = models.TextField(
        verbose_name="Nombre del área",
        blank=True, null=True)
    description = models.TextField(
        verbose_name="Descripción del área",
        blank=True, null=True)

    def __str__(self):
        return self.key or self.name

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

