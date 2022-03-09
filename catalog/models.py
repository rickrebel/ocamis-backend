# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.postgres.fields import JSONField


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
        db_table = u'desabasto_state'


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

    class Meta:
        verbose_name = u"Institución"
        verbose_name_plural = u"Instituciones"
        db_table = u'desabasto_institution'


@python_2_unicode_compatible
class CLUES(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    #state = models.IntegerField()
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    #institution = models.IntegerField()
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
    alternative_names = JSONField(blank=True, null=True)

    def __str__(self):
        return self.clues

    class Meta:
        verbose_name = u"Catálogo ClUES"
        verbose_name_plural = u"Catálogo ClUESs"
        db_table = u'desabasto_clues'


@python_2_unicode_compatible
class Alliances(models.Model):
    name = models.CharField(max_length=180)
    page_url = models.CharField(max_length=180, blank=True, null=True)
    logo = models.FileField()
    level = models.IntegerField(default=2)

    class Meta:
        verbose_name = u"Alianza"
        verbose_name_plural = u"Alianzas"
        db_table = u'desabasto_alliances'

    def __str__(self):
        return self.name
