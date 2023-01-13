# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField


class State(models.Model):
    def default_alternative_names():
        return []
    inegi_code = models.CharField(max_length=2, verbose_name=u"Clave INEGI")
    name = models.CharField(max_length=50, verbose_name=u"Nombre")
    short_name = models.CharField(
        max_length=20, verbose_name=u"Nombre Corto",
        blank=True, null=True)
    code_name = models.CharField(
        max_length=6, verbose_name=u"Nombre Clave",
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
        verbose_name = u"Estado"
        verbose_name_plural = u"Estados"
        db_table = u'desabasto_state'


class Municipality(models.Model):
    inegi_code = models.CharField(max_length=6, verbose_name=u"Clave INEGI")
    name = models.CharField(max_length=120, verbose_name=u"Nombre")
    state = models.ForeignKey(
        State, verbose_name="Entidad",
        null=True, on_delete=models.CASCADE,
        related_name="municipalities")

    def __str__(self):
        return u"%s - %s" % (self.name, self.state)

    class Meta:
        verbose_name = u"Municipio"
        verbose_name_plural = u"Municipios"


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

    class Meta:
        verbose_name = u"Institución"
        verbose_name_plural = u"Instituciones"
        db_table = u'desabasto_institution'


class Tipology(models.Model):
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
        verbose_name = u"Tipología"
        verbose_name_plural = u"Tipologías"


class CLUES(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    #state = models.IntegerField()
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE)
    #institution = models.IntegerField()
    name = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE LA UNIDAD")
    is_searchable = models.BooleanField(
        default=False, verbose_name=u"Activo",
        help_text="Puede buscarse por el usuario")
    municipality = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DEL MUNICIPIO")
    municipality_inegi_code = models.ForeignKey(
        Municipality, on_delete=models.CASCADE)
    tipology = models.CharField(
        max_length=255, verbose_name=u"NOMBRE DE TIPOLOGIA")
    tipology_obj = models.ForeignKey(
        Tipology, verbose_name=u"Tipología (Catálogo)",
        blank=True, null=True, on_delete=models.CASCADE)
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
    alternative_names = JSONField(blank=True, null=True)
    
    #Nuevos fields
    type_street = models.CharField(
        max_length=80, blank=True, null=True, 
        verbose_name=u"TIPO DE VIALIDAD")
    street = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"VIALIDAD")    
    streat_number = models.CharField(
        max_length=80, blank=True, null=True, 
        verbose_name=u"NÚMERO CALLE")
    suburb = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name=u"SUBURBIO")
    postal_code = models.CharField(
        max_length=6, blank=True, null=True,
        verbose_name=u"CODIGO POSTAL")
    rfc = models.CharField(
        max_length=6, blank=True, null=True,
        verbose_name=u"RFC")
    last_change = models.DateTimeField(
        blank=True, null=True,
         verbose_name=u"FECHA ULTIMO MOVIMIENTO")

    def __str__(self):
        return self.clues

    class Meta:
        verbose_name = u"Hospital o clínica CLUES"
        verbose_name_plural = u"Catálogo CLUES"
        db_table = u'desabasto_clues'


class Delegation(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"Nombre")
    institution = models.ForeignKey(
        Institution, verbose_name="Institución",
        on_delete=models.CASCADE)
    state = models.ForeignKey(
        State, verbose_name="Entidad",
        on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True,
        on_delete=models.CASCADE)
    other_names = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s --%s" % (
            self.name, self.state, self.institution)

    class Meta:
        verbose_name = u"Delegación"
        verbose_name_plural = u"Delegaciones"


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
        verbose_name=u"Número de contacto")

    class Meta:
        verbose_name = u"Alianza"
        verbose_name_plural = u"Alianzas"
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
        max_length=20, verbose_name=u"Siglas del Sujeto Obligado",
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
    vigencia = models.NullBooleanField(
        default=True, help_text="Actualmente se le sigue preguntando")
    competent = models.BooleanField(
        default=True,
        verbose_name="Competente",
        help_text="Es Competente porque tiene pacientes y debe tener la información")
    notes = models.TextField(blank=True, null=True)
    is_pilot = models.BooleanField(default=False)
    population = models.IntegerField(
        verbose_name="Derechohabientes", blank=True, null=True)

    def __str__(self):
        return self.name or u"%s -%s -%s" % (
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
        verbose_name = u"Sujeto Obligado"
        verbose_name_plural = u"Sujetos Obligados"
