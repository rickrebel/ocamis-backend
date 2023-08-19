from django.db import models

from inai.models import DataFile, SheetFile, LapSheet
from data_param.models import NameColumn
from django.db.models import JSONField
import uuid as uuid_lib

from med_cat.models import (
    Doctor, Diagnosis, Area, MedicalUnit, Medicament, Delivered)


class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Especialidad de Médico"
        verbose_name_plural = "Especialidades de Médicos"

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"

    def __str__(self):
        return self.name


class Rx(models.Model):
    from geo.models import CLUES, Delegation, Entity
    uuid_folio = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    folio_ocamis = models.CharField(max_length=64)
    folio_document = models.CharField(max_length=46)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField()
    iso_year = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    medical_unit = models.ForeignKey(
        MedicalUnit, on_delete=models.CASCADE, blank=True, null=True)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, blank=True, null=True)
    delivered_final = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    # EXTENSION: COSAS NO TAN RELEVANTES:
    # document_type = models.ForeignKey(
    #     DocumentType, on_delete=models.CASCADE, blank=True, null=True)
    document_type = models.CharField(max_length=50, blank=True, null=True)
    date_release = models.DateTimeField(blank=True, null=True)
    date_visit = models.DateTimeField(blank=True, null=True)
    date_delivery = models.DateTimeField(blank=True, null=True)
    doctor = models.ForeignKey(
        Doctor, blank=True, null=True, on_delete=models.CASCADE)
    diagnosis = models.ForeignKey(
        Diagnosis, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        db_table = 'formula_rx'

    def __str__(self):
        return self.folio_ocamis


class Drug(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    rx = models.ForeignKey(
        Rx, on_delete=models.CASCADE,
        related_name='drugs')
    # sheet_file = models.ForeignKey(
    #     SheetFile, on_delete=models.CASCADE)
    sheet_file_id = models.IntegerField()
    row_seq = models.PositiveIntegerField(blank=True, null=True)
    # lap_sheet = models.ForeignKey(
    #     LapSheet, on_delete=models.CASCADE)
    lap_sheet_id = models.IntegerField()

    medicament = models.ForeignKey(
        Medicament, blank=True, null=True,
        on_delete=models.CASCADE)
    prescribed_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    delivered_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    date_closed = models.DateTimeField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    entity_week_id = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"

    def __str__(self):
        return str(self.uuid)


class MissingRow(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    sheet_file = models.ForeignKey(
        SheetFile, on_delete=models.CASCADE, related_name='missing_rows')
    # row_seq = models.IntegerField(default=1)
    # tab = models.CharField(max_length=255, blank=True, null=True)

    # ¡ÚLTIMOS CAMPOS SIEMPRE!
    drug = models.ForeignKey(
        Drug, blank=True, null=True,
        on_delete=models.CASCADE)
    original_data = JSONField(blank=True, null=True)
    inserted = models.BooleanField(blank=True, null=True)
    # errors = JSONField(blank=True, null=True, default=list)
    error = models.TextField(blank=True, null=True)
    # !!! Por nada del mundo, poner más campos debajo de este comentario

    def __str__(self):
        #return "%s -- %s" % (self.file, self.recipe_report or self.recipe_medicine)
        return self.sheet_file

    class Meta:
        verbose_name = "Renglón faltante"
        verbose_name_plural = "Renglones faltantes"


class MissingField(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    missing_row = models.ForeignKey(
        MissingRow, on_delete=models.CASCADE)
    # name_column = models.IntegerField(blank=True, null=True)
    name_column = models.ForeignKey(
        NameColumn, on_delete=models.CASCADE)
    # SIEMPRE EN POSICIÓN 3:
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(blank=True, null=True)
    last_revised = models.DateTimeField()

    # ¡ÚLTIMOS CAMPOS SIEMPRE!
    inserted = models.BooleanField(blank=True, null=True)
    # errors = JSONField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    # !!! Por nada del mundo, poner más campos debajo de este comentario

    def __str__(self):
        return "%s -- %s" % (self.missing_row, self.name_column)

    class Meta:
        verbose_name = "Documento Faltante"
        verbose_name_plural = "Documentos Faltantes"
