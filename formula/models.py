from django.db import models

from inai.models import NameColumn, DataFile
from django.db.models import JSONField
import uuid


class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Especialidad de Médico"
        verbose_name_plural = "Especialidades de Médicos"

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=50)

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
    from catalog.models import Institution
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    clave_doctor = models.CharField(max_length=30, blank=True, null=True)
    institution = models.ForeignKey(
        Institution, null=True, blank=True, on_delete=models.CASCADE)
    nombre_medico = models.CharField(max_length=255)
    especialidad_medico = models.ForeignKey(
        MedicalSpeciality, on_delete=models.CASCADE, blank=True, null=True)
    professional_license = models.CharField(max_length=20, blank=True, null=True)
    #especialidad_medico = models.IntegerField()

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctores"

    def __str__(self):
        return str(self.clave_doctor)


class Prescription(models.Model):
    from catalog.models import CLUES, Delegation, Area
    from inai.models import DataFile
    #Nueva versión del modelo Prescription con atomizado de datos
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    folio_ocamis = models.CharField(max_length=60)
    # folio_document = models.CharField(max_length=40)
    folio_document = models.CharField(max_length=40)
    iso_year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    #delegation = models.IntegerField(blank=True, null=True)
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE)
    clues = models.ForeignKey(
        CLUES, blank=True, null=True, on_delete=models.CASCADE)
    #clues = models.IntegerField(blank=True, null=True)
    #medico = models.CharField(max_length=48, blank=True, null=True)
    #year_month = models.IntegerField(blank=True, null=True)
    #delivered = models.CharField(max_length=3, blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    #anomaly = models.TextField(blank=True, null=True)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, blank=True, null=True)
    #EXTENSION: COSAS NO TAN RELEVANTES:
    #tipo_documento = models.IntegerField()
    type_document = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE, blank=True, null=True)

    # fecha_emision = models.DateTimeField(blank=True, null=True)
    date_release = models.DateTimeField(blank=True, null=True)
    # fecha_entrega = models.DateTimeField(blank=True, null=True)
    date_delivery = models.DateTimeField(blank=True, null=True)
    date_visit = models.DateTimeField(blank=True, null=True)
    doctor = models.ForeignKey(
        Doctor, blank=True, null=True, on_delete=models.CASCADE)
    # clave_presupuestal = models.CharField(
    #     max_length=20, blank=True, null=True)
    budget_key = models.CharField(
        max_length=20, blank=True, null=True)

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

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    container = models.ForeignKey(
        Container, blank=True, null=True, on_delete=models.CASCADE)
    # cantidad_prescrita = models.PositiveSmallIntegerField(
    #     blank=True, null=True)
    prescribed_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    # cantidad_entregada = models.PositiveSmallIntegerField(
    #     blank=True, null=True)
    delivered_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    not_delivered_amount = models.PositiveSmallIntegerField(
        blank=True, null=True)
    #delivered = models.CharField(max_length=3, blank=True, null=True)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    #OTROS DATOS NO TAN RELEVANTES:
    # precio_medicamento = models.FloatField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    row_seq = models.PositiveIntegerField(blank=True, null=True)
    rn = models.CharField(max_length=80, blank=True, null=True)
    for_training = models.CharField(
        max_length=20, choices=TRAINING_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"

    def __str__(self):
        return str(self.rn)


class MissingRow(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        DataFile, on_delete=models.CASCADE)
    prescription = models.ForeignKey(
        Prescription, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    drug = models.ForeignKey(
        Drug,
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
        verbose_name = "Renglón faltante"
        verbose_name_plural = "Renglones faltantes"


class MissingField(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    missing_row = models.ForeignKey(
        MissingRow,
        on_delete=models.CASCADE)
    name_column = models.ForeignKey(
        NameColumn,
        on_delete=models.CASCADE)
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(
        blank=True, null=True)
    errors = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.missing_row, self.column)

    class Meta:
        verbose_name = "Documento Faltante"
        verbose_name_plural = "Documentos Faltantes"


class Diagnosis(models.Model):

    cie10 = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    motive = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"

    def __str__(self):
        return self.cie10 or self.text or self.reason
