from django.db import models

from inai.models import DataFile, SheetFile
from data_param.models import NameColumn
from django.db.models import JSONField
import uuid as uuid_lib

from med_cat.models import Doctor, Diagnosis, Area, MedicalUnity


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


class Delivered(models.Model):
    short_name = models.CharField(
        max_length=20, primary_key=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Clasificación de entrega"
        verbose_name_plural = "Clasificaciones de Entrega"

    def __str__(self):
        return self.name


class Prescription(models.Model):
    from geo.models import CLUES, Delegation, Entity
    uuid_folio = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    folio_ocamis = models.CharField(max_length=60)
    folio_document = models.CharField(max_length=40)
    iso_year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    medical_unity = models.ForeignKey(MedicalUnity, on_delete=models.CASCADE)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, blank=True, null=True)
    # delegation = models.ForeignKey(
    #     Delegation, on_delete=models.CASCADE, blank=True, null=True)
    # clues = models.ForeignKey(
    #     CLUES, blank=True, null=True, on_delete=models.CASCADE)
    delivered_final = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    # EXTENSION: COSAS NO TAN RELEVANTES:
    # document_type = models.ForeignKey(
    #     DocumentType, on_delete=models.CASCADE, blank=True, null=True)
    document_type = models.CharField(max_length=50, blank=True, null=True)
    date_release = models.DateTimeField(blank=True, null=True)
    date_delivery = models.DateTimeField(blank=True, null=True)
    date_visit = models.DateTimeField(blank=True, null=True)
    doctor = models.ForeignKey(
        Doctor, blank=True, null=True, on_delete=models.CASCADE)
    diagnosis = models.ForeignKey(
        Diagnosis, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"

    def __str__(self):
        return self.folio_ocamis


class Drug(models.Model):
    from medicine.models import Container

    uuid = models.UUIDField(primary_key=True, default=uuid_lib.uuid4, editable=False)
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE,
        related_name='drugs')
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    sheet_name = models.CharField(max_length=255, blank=True, null=True)
    row_seq = models.PositiveIntegerField(blank=True, null=True)

    container = models.ForeignKey(
        Container, blank=True, null=True, on_delete=models.CASCADE)
    prescribed_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    delivered_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    # OTROS DATOS NO TAN RELEVANTES:
    price = models.FloatField(blank=True, null=True)
    # rn = models.CharField(max_length=80, blank=True, null=True)
    # for_training = models.CharField(
    #     max_length=20, choices=TRAINING_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"

    def __str__(self):
        return str(self.rn)


class MissingRow(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    sheet_file = models.ForeignKey(
        SheetFile, on_delete=models.CASCADE, related_name='missing_rows')
    # data_file = models.ForeignKey(
    #     DataFile, on_delete=models.CASCADE)
    # sheet_name = models.CharField(max_length=255, blank=True, null=True)
    # prescription = models.ForeignKey(
    #     Prescription,
    #     blank=True, null=True,
    #     on_delete=models.CASCADE, related_name='missing_rows')
    drug = models.ForeignKey(
        Drug, blank=True, null=True,
        on_delete=models.CASCADE)
    original_data = JSONField(blank=True, null=True)
    # row_seq = models.IntegerField(default=1)
    # tab = models.CharField(max_length=255, blank=True, null=True)

    # ¡ÚLTIMOS CAMPOS SIEMPRE!
    inserted = models.BooleanField(blank=True, null=True)
    # errors = JSONField(blank=True, null=True, default=list)
    error = models.TextField(blank=True, null=True)
    # !!! Por nada del mundo, poner más campos debajo de este comentario

    def __str__(self):
        #return "%s -- %s" % (self.file, self.recipe_report or self.recipe_medicine)
        return self.data_file

    class Meta:
        verbose_name = "Renglón faltante"
        verbose_name_plural = "Renglones faltantes"


class MissingField(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    missing_row = models.ForeignKey(
        MissingRow,
        on_delete=models.CASCADE)
    # name_column = models.IntegerField(blank=True, null=True)
    name_column = models.ForeignKey(
        NameColumn, on_delete=models.CASCADE)
    # SIEMPRE EN POSICIÓN 3:
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(
        blank=True, null=True)
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
