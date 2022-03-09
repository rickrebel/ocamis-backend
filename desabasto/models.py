# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.core.validators import validate_email
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "DocumentType"
        verbose_name_plural = "DocumentTypes"

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
    #especialidad_medico = models.ForeignKey(
    #    MedicalSpeciality, on_delete=models.CASCADE)
    especialidad_medico = models.IntegerField()

    class Meta:
        verbose_name = "Medic"
        verbose_name_plural = "Medics"

    def __str__(self):
        return str(self.clave_medico)


"""@python_2_unicode_compatible
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
        return self.folio_documento"""


"""@python_2_unicode_compatible
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
        return str(self.rn)"""


@python_2_unicode_compatible
class RecipeReport2(models.Model):
    """Nueva vercion del modelo Recipe con atomizado de datos"""
    folio_ocamis = models.CharField(max_length=48, primary_key=True)
    #tipo_documento = models.ForeignKey(
    #    DocumentType, on_delete=models.CASCADE)
    tipo_documento = models.IntegerField()
    folio_documento = models.CharField(max_length=40)
    iso_year = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_week = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)

    #delegacion = models.ForeignKey(
    #    State, blank=True, null=True, on_delete=models.CASCADE)
    delegacion = models.IntegerField(blank=True, null=True)
    #clues = models.ForeignKey(
    #    CLUES, blank=True, null=True, on_delete=models.CASCADE)
    clues = models.IntegerField(blank=True, null=True)
    #medico = models.ForeignKey(
    #    Medic, blank=True, null=True, on_delete=models.CASCADE)
    medico = models.CharField(max_length=48, blank=True, null=True)

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
    #recipe = models.ForeignKey(RecipeReport2, on_delete=models.CASCADE)
    recipe = models.CharField(max_length=48)

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
