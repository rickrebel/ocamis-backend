from django.db import models

from respond.models import DataFile, SheetFile, LapSheet
from inai.models import WeekRecord
from data_param.models import NameColumn
from django.db.models import JSONField
import uuid as uuid_lib

from rds.models import Cluster
from med_cat.models import (
    Doctor, Diagnosis, Area, MedicalUnit, Medicament, Delivered)
from geo.models import CLUES, Delegation, Provider
from medicine.models import Component, Presentation, Container, ViewMedicine


class MedicalSpeciality(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Especialidad de Médico"
        verbose_name_plural = "Especialidades de Médicos"

    def __str__(self):
        return self.name


class Rx(models.Model):
    uuid_folio = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    folio_ocamis = models.CharField(max_length=70)
    folio_document = models.CharField(max_length=46)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField()
    iso_year = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    iso_day = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    medical_unit = models.ForeignKey(
        MedicalUnit, on_delete=models.CASCADE, blank=True, null=True)
    # area = models.ForeignKey(
    #     Area, on_delete=models.CASCADE, blank=True, null=True)
    delivered_final = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, blank=True, null=True)
    # EXTENSION: COSAS NO TAN RELEVANTES:
    document_type = models.CharField(max_length=50, blank=True, null=True)
    date_release = models.DateTimeField(blank=True, null=True)
    date_visit = models.DateTimeField(blank=True, null=True)
    date_delivery = models.DateTimeField(blank=True, null=True)
    days_between = models.PositiveSmallIntegerField(blank=True, null=True)
    doctor = models.ForeignKey(
        Doctor, blank=True, null=True, on_delete=models.CASCADE)
    # artificial_folio = models.BooleanField(default=False)
    # diagnosis = models.ForeignKey(
    #     Diagnosis, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"

    def __str__(self):
        return self.folio_ocamis


class Drug(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    rx = models.ForeignKey(
        Rx, on_delete=models.CASCADE, related_name='drugs')
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
    # date_created = models.DateTimeField(blank=True, null=True)
    # date_closed = models.DateTimeField(blank=True, null=True)
    # price = models.FloatField(blank=True, null=True)
    week_record_id = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"

    def __str__(self):
        return str(self.uuid)


class ComplementRx(models.Model):
    uuid_comp_rx = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    rx = models.ForeignKey(
        Rx, on_delete=models.CASCADE,
        related_name='complements')
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    record = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Expediente')
    personal_number = models.CharField(
        max_length=80, blank=True, null=True, verbose_name='Número personal')
    gender = models.CharField(
        max_length=30, blank=True, null=True, verbose_name='Género')
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, blank=True, null=True)
    # diagnosis = models.ForeignKey(
    #     Diagnosis, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Complemento de Receta"
        verbose_name_plural = "Complementos de Receta"

    def __str__(self):
        return str(self.uuid_comp_rx)


class DiagnosisRx(models.Model):
    # ⚠️¡No modificar estructura de los primeros 4 campos!
    uuid_diag_rx = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    rx = models.ForeignKey(
        Rx, on_delete=models.CASCADE,
        related_name='diagnoses')
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    is_main = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Diagnóstico por Receta"
        verbose_name_plural = "Diagnósticos por Receta"

    def __str__(self):
        return str(self.uuid_diag_rx)


class ComplementDrug(models.Model):
    uuid_comp_drug = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    drug = models.ForeignKey(
        Drug, on_delete=models.CASCADE,
        related_name='complements')
    lote = models.CharField(
        max_length=80, blank=True, null=True, verbose_name='Lote')
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name='Fecha de caducidad')
    price = models.FloatField(blank=True, null=True)
    total_price = models.FloatField(blank=True, null=True)
    # TODO: Agregar campo de marca
    # brand = models.CharField(
    #     max_length=255, blank=True, null=True, verbose_name='Marca')

    class Meta:
        verbose_name = "Insumos"
        verbose_name_plural = "Insumos (medicamentos)"

    def __str__(self):
        return str(self.uuid_comp_drug)


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
        # return "%s -- %s" % (self.file, self.recipe_report or self.recipe_medicine)
        return self.sheet_file

    class Meta:
        verbose_name = "Renglón faltante"
        verbose_name_plural = "Renglones faltantes"


class MissingField(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    missing_row = models.ForeignKey(
        MissingRow, on_delete=models.CASCADE)
    name_column = models.ForeignKey(NameColumn, on_delete=models.CASCADE)
    # ⚠️SIEMPRE EN POSICIÓN 3:
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(blank=True, null=True)
    last_revised = models.DateTimeField()
    # ⚠️¡ÚLTIMOS CAMPOS SIEMPRE!
    inserted = models.BooleanField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    # !!! Por nada del mundo, poner más campos debajo de este comentario

    def __str__(self):
        return "%s -- %s" % (self.missing_row, self.name_column)

    class Meta:
        verbose_name = "Documento Faltante"
        verbose_name_plural = "Documentos Faltantes"


class MatDrugPriority(models.Model):

    # cluster = models.ForeignKey(
    #     Cluster, on_delete=models.DO_NOTHING,
    #     blank=True, null=True, default='first')
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
    clues = models.ForeignKey(
        CLUES, on_delete=models.CASCADE, blank=True, null=True)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.CASCADE)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE)
    key = models.CharField(max_length=255, blank=True, null=True)
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, blank=True, null=True)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_priority'

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.week_record, self.delivered, self.container, self.key)


# SELECT
# 	week.iso_year,
# 	week.iso_week,
# 	week.entity_id,
# 	week.year,
# 	week.month,
# 	drug.delivered_id,
# 	drug.medicament_id,
#   COALESCE(sum(drug.prescribed_amount), 0) AS prescribed_total,
#   COALESCE(sum(drug.delivered_amount), 0) AS delivered_total,
# 	COUNT(*) as total
# FROM fm_55_201907_drug drug
# JOIN inai_entityweek week ON drug.entity_week_id = week.id
# GROUP BY
#     week.iso_year,
#     week.iso_week,
#     week.entity_id,
#     week.year,
#     week.month,
# 	drug.delivered_id,
# 	drug.medicament_id;


class MatDrugEntity(models.Model):
    iso_year = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    entity = models.ForeignKey(
        Provider, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE)
    medicament = models.ForeignKey(
        Medicament, on_delete=models.CASCADE)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_entity'

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.iso_year, self.iso_week, self.delivered, self.medicament)


# ViewDrugEntity2
# SELECT
# 	gen_random_uuid() AS uuid,
# 	'CLUSTER_NAME'::text AS cluster_id,
# 	drug.week_record_id,
# 	drug.delivered_id,
# 	drug.medicament_id,
# 	COALESCE(sum(drug.prescribed_amount), 0) AS prescribed_total,
# 	COALESCE(sum(drug.delivered_amount), 0) AS delivered_total,
# 	count(*) AS total
# FROM formula_drug drug
# GROUP BY
# 	drug.week_record_id,
# 	drug.delivered_id,
# 	drug.medicament_id;


class MatDrugEntity2(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    cluster = models.ForeignKey(
        Cluster, on_delete=models.DO_NOTHING, default='first')
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.DO_NOTHING)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.DO_NOTHING)
    medicament = models.ForeignKey(
        Medicament, on_delete=models.DO_NOTHING)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_entity2'

    def __str__(self):
        return f"{self.week_record} -- {self.delivered} -- {self.medicament}"


# ViewDrugEntity2
# SELECT
# 	gen_random_uuid() AS uuid,
# 	drug.cluster_id,
# 	week.provider_id,
# 	drug.week_record_id,
# 	week.year AS year,
# 	week.month AS month,
# 	week.iso_week AS iso_week,
# 	week.iso_year AS iso_year,
# 	medicine.id AS medicine_id,
# 	COALESCE(sum(drug.prescribed_amount), 0) AS prescribed_total,
# 	COALESCE(sum(drug.delivered_amount), 0) AS delivered_total,
# 	COALESCE(sum(drug.total), 0) AS total
# FROM mat_drug_entity2 drug
# LEFT JOIN view_medicine medicine ON drug.medicament_id = medicine.container_id
# JOIN inai_entityweek week ON drug.week_record_id = week.id
# GROUP BY
# 	drug.cluster_id,
# 	drug.delegation_id,
# 	drug.week_record_id,
# 	drug.delivered_id,
# 	drug.medicament_id;


class ViewDrugEntity2(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.DO_NOTHING)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    year_week = models.CharField(max_length=10)
    iso_week = models.PositiveSmallIntegerField()
    iso_year = models.PositiveSmallIntegerField()
    provider = models.ForeignKey(Provider, on_delete=models.DO_NOTHING)
    medicine = models.ForeignKey(ViewMedicine, on_delete=models.DO_NOTHING)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'view_drug_entity2'

    def __str__(self):
        return f"{self.week_record} -- {self.medicine}"


class MatDrug(models.Model):
    key = models.CharField(max_length=255)
    clues = models.ForeignKey(
        CLUES, on_delete=models.CASCADE)
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.CASCADE)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE)
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug'

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.week_record, self.delivered, self.container, self.key)


class MatDrugExtended(models.Model):
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE)
    iso_year = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE)
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE)
    presentation = models.ForeignKey(
        Presentation, on_delete=models.CASCADE)
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_extended'

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.iso_year, self.iso_week, self.provider, self.component)


class MatDrugTotals(models.Model):

    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
    clues = models.ForeignKey(
        CLUES, on_delete=models.CASCADE, blank=True, null=True)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.CASCADE)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_totals'

    def __str__(self):
        return "%s -- %s -- %s" % (
            self.week_record, self.delivered, self.clues)


class MatDrugTotals2(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    cluster = models.ForeignKey(
        Cluster, on_delete=models.DO_NOTHING,
        blank=True, null=True, default='first')
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.CASCADE)
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE)
    prescribed_total = models.IntegerField()
    delivered_total = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        db_table = 'mat_drug_totals2'

    def __str__(self):
        return "%s -- %s -- %s" % (
            self.week_record, self.delivered, self.clues)
