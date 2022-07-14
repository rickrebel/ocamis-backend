# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "MedicalSpeciality"
        verbose_name_plural = "MedicalSpecialitys"
        db_table = u'desabasto_medicalspeciality'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "DocumentType"
        verbose_name_plural = "DocumentTypes"
        db_table = u'desabasto_documenttype'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Medic(models.Model):
    from catalog.models import Institution
    clave_medico = models.CharField(primary_key=True, max_length=30)
    institution = models.ForeignKey(
        Institution, null=True, blank=True, on_delete=models.CASCADE)
    nombre_medico = models.CharField(max_length=255)
    especialidad_medico = models.ForeignKey(
        MedicalSpeciality, on_delete=models.CASCADE, blank=True, null=True)
    #especialidad_medico = models.IntegerField()

    class Meta:
        verbose_name = "Medic"
        verbose_name_plural = "Medics"
        db_table = u'medic'

    def __str__(self):
        return str(self.clave_medico)


class RecipeReport2(models.Model):
    from catalog.models import CLUES, State
    """Nueva vercion del modelo Recipe con atomizado de datos"""
    folio_ocamis = models.CharField(max_length=48, primary_key=True)
    tipo_documento = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE)
    #tipo_documento = models.IntegerField()
    folio_documento = models.CharField(max_length=40)
    iso_year = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_week = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)

    delegacion = models.ForeignKey(
        State, blank=True, null=True, on_delete=models.CASCADE)
    #delegacion = models.IntegerField(blank=True, null=True)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    #clues = models.IntegerField(blank=True, null=True)
    medico = models.ForeignKey(
        Medic, blank=True, null=True, on_delete=models.CASCADE)
    #medico = models.CharField(max_length=48, blank=True, null=True)

    year_month = models.IntegerField(blank=True, null=True)
    clave_presupuestal = models.CharField(
        max_length=20, blank=True, null=True)
    nivel_atencion = models.IntegerField(blank=True, null=True)
    delivered = models.CharField(max_length=3, blank=True, null=True)
    anomaly = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        db_table = u'desabasto_recipereport2'

    def __str__(self):
        return self.folio_documento


@python_2_unicode_compatible
class RecipeMedicine2(models.Model):
    from medicine.models import Container
    recipe = models.ForeignKey(RecipeReport2, on_delete=models.CASCADE)
    #recipe = models.CharField(max_length=48)

    #clave_medicamento = models.CharField(max_length=20, blank=True, null=True)
    container = models.ForeignKey(
        Container, blank=True, null=True, on_delete=models.CASCADE)
    cantidad_prescrita = models.IntegerField(blank=True, null=True)
    cantidad_entregada = models.IntegerField(blank=True, null=True)

    precio_medicamento = models.FloatField(blank=True, null=True)
    rn = models.IntegerField(blank=True, null=True)

    delivered = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"
        db_table = u'desabasto_recipemedicine2'

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
        db_table = u'desabasto_recipereportlog'

    def __str__(self):
        return self.folio_documento
