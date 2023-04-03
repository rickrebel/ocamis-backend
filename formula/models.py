from django.db import models

from inai.models import DataFile, SheetFile
from data_param.models import NameColumn
from django.db.models import JSONField
import uuid as uuid_lib


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


class Doctor(models.Model):
    from catalog.models import Institution, Delegation
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    clave = models.CharField(max_length=30, blank=True, null=True)
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE)
    delegation = models.ForeignKey(
        Delegation, null=True, blank=True, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    # especialidad_medico = models.CharField(max_length=255, blank=True, null=True)
    medical_speciality = models.CharField(max_length=255, blank=True, null=True)
    professional_license = models.CharField(max_length=20, blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)
    #especialidad_medico = models.IntegerField()

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctores"

    def __str__(self):
        return str(self.clave)


class Diagnosis(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    cie10 = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    motive = models.TextField(blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"

    def __str__(self):
        return self.cie10 or self.text or self.motive


class Prescription(models.Model):
    from catalog.models import CLUES, Delegation, Area
    uuid_folio = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    folio_ocamis = models.CharField(max_length=60)
    folio_document = models.CharField(max_length=40)
    iso_year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    delivered_final = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, blank=True, null=True)
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
    # is_valid = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"

    def __str__(self):
        return self.folio_ocamis


class Drug(models.Model):
    from medicine.models import Container

    TRAINING_CHOICES = (
        ('medicine', 'Medicamentos'),
        ('clues', 'CLUES'),
        ('jurisdiction', 'Jurisdicción'),
        ('delivered', 'Clasificación Entrega'),
        ('diagnosis', 'Diagnóstico'),
    )

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
