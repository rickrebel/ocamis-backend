# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from files_rows.models import Column, File
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible

class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "MedicalSpeciality"
        verbose_name_plural = "MedicalSpecialitys"
        db_table = u'desabasto_medicalspeciality'

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "DocumentType"
        verbose_name_plural = "DocumentTypes"
        db_table = u'desabasto_documenttype'

    def __str__(self):
        return self.name


class Delivered(models.Model):
    short_name = models.CharField(
        max_length=3, primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Clasificación de entrega"
        verbose_name_plural = "Clasificaciones de Entrega"

    def __str__(self):
        return self.name


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


@python_2_unicode_compatible
class Recipe(models.Model):
    from catalog.models import CLUES, Delegation
    from files_rows.models import File
    #Nueva versión del modelo Recipe con atomizado de datos
    folio_ocamis = models.CharField(max_length=48, primary_key=True)
    iso_year = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_week = models.PositiveSmallIntegerField(blank=True, null=True)
    #delegacion = models.IntegerField(blank=True, null=True)
    delegacion = models.ForeignKey(
        Delegation, blank=True, null=True, on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    #clues = models.IntegerField(blank=True, null=True)
    #medico = models.CharField(max_length=48, blank=True, null=True)
    #year_month = models.IntegerField(blank=True, null=True)
    #delivered = models.CharField(max_length=3, blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    #anomaly = models.TextField(blank=True, null=True)
    
    #EXTENSION: COSAS NO TAN RELEVANTES:
    folio_documento = models.CharField(max_length=40)
    #tipo_documento = models.IntegerField()
    type_document = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE)
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    medico = models.ForeignKey(
        Medic, blank=True, null=True, on_delete=models.CASCADE)
    clave_presupuestal = models.CharField(
        max_length=20, blank=True, null=True)
    #nivel_atencion = models.IntegerField(blank=True, null=True)
    file = models.ForeignKey(
        File, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        db_table = u'desabasto_recipereport2'

    def __str__(self):
        return self.folio_ocamis


@python_2_unicode_compatible
class Medicine(models.Model):
    from medicine.models import Container
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    #recipe = models.CharField(max_length=48)
    #clave_medicamento = models.CharField(max_length=20, blank=True, null=True)
    container = models.ForeignKey(
        Container, blank=True, null=True, on_delete=models.CASCADE)
    cantidad_prescrita = models.PositiveSmallIntegerField(
        blank=True, null=True)
    cantidad_entregada = models.PositiveSmallIntegerField(
        blank=True, null=True)
    #delivered = models.CharField(max_length=3, blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    #OTROS DATOS NO TAN RELEVANTES:
    precio_medicamento = models.FloatField(blank=True, null=True)
    row_seq = models.PositiveIntegerField(blank=True, null=True)
    #rn = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"
        db_table = u'desabasto_recipemedicine2'

    def __str__(self):
        return str(self.rn)


"""class RecipeLog(models.Model):
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
        verbose_name = "RecipeLog"
        verbose_name_plural = "RecipeLogs"
        db_table = u'desabasto_recipereportlog'

    def __str__(self):
        return self.folio_documento """


class MissingRow(models.Model):
    file = models.ForeignKey(
        File, on_delete=models.CASCADE)
    recipe_report = models.ForeignKey(
        Recipe, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    recipe_medicine = models.ForeignKey(
        Medicine, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    original_data = JSONField(
        blank=True, null=True)
    row_seq = models.IntegerField(default=1)
    #tab = models.CharField(max_length=255, blank=True, null=True)
    errors = JSONField(blank=True, null=True)

    def __str__(self):
        #return "%s -- %s" % (self.file, self.recipe_report or self.recipe_medicine)
        return self.file

    class Meta:
        verbose_name = u"Renglón faltante"
        verbose_name_plural = u"Renglones faltantes"


class MissingField(models.Model):
    missing_row = models.ForeignKey(
        MissingRow,
        on_delete=models.CASCADE)
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE)
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(
        blank=True, null=True)
    errors = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.missing_row, self.column)

    class Meta:
        verbose_name = u"Documento Faltante"
        verbose_name_plural = u"Documentos Faltantes"

