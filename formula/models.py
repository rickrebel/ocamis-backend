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

    def __str__(self):
        return self.folio_ocamis

#
# class MiniRx(models.Model):
#     from geo.models import CLUES, Delegation, Entity
#     uuid_folio = models.UUIDField(
#         primary_key=True, default=uuid_lib.uuid4, editable=False)
#     entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
#     folio_ocamis = models.CharField(max_length=64)
#     entity_week = models.ForeignKey(
#         "EntityWeek", on_delete=models.CASCADE, blank=True, null=True)
#     medical_unit = models.ForeignKey(
#         MedicalUnit, on_delete=models.CASCADE, blank=True, null=True)
#     area = models.ForeignKey(
#         Area, on_delete=models.CASCADE, blank=True, null=True)
#     delivered_final = models.ForeignKey(
#         Delivered, on_delete=models.CASCADE, blank=True, null=True)
#     document_type = models.ForeignKey(
#         "DocumentType", on_delete=models.CASCADE, blank=True, null=True)
#     doctor = models.ForeignKey(
#         Doctor, blank=True, null=True, on_delete=models.CASCADE)
#     diagnosis = models.ForeignKey(
#         Diagnosis, blank=True, null=True, on_delete=models.CASCADE)
#
#     class Meta:
#         verbose_name = "Receta"
#         verbose_name_plural = "Recetas"
#         db_table = 'formula_rx'
#
#     def __str__(self):
#         return self.folio_ocamis


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


# class ComplementRx(models.Model):
#     uuid = models.UUIDField(
#         primary_key=True, default=uuid_lib.uuid4, editable=False)
#     rx = models.ForeignKey(
#         Rx, on_delete=models.CASCADE,
#         related_name='complements')
#     age = models.PositiveSmallIntegerField(blank=True, null=True)
#     record = models.CharField(
#         max_length=255, blank=True, null=True, verbose_name='Expediente')
#     personal_number = models.CharField(
#         max_length=80, blank=True, null=True, verbose_name='Número personal')
#     gender = models.CharField(
#         max_length=30, blank=True, null=True, verbose_name='Género')
#     area = models.ForeignKey(
#         Area, on_delete=models.CASCADE, blank=True, null=True)
#     diagnosis = models.ForeignKey(
#         Diagnosis, blank=True, null=True, on_delete=models.CASCADE)
#
#     class Meta:
#         verbose_name = "Complemento de Receta"
#         verbose_name_plural = "Complementos de Receta"
#
#     def __str__(self):
#         return str(self.uuid)
#
#
# class ComplementDrug(models.Model):
#     uuid = models.UUIDField(
#         primary_key=True, default=uuid_lib.uuid4, editable=False)
#     drug = models.ForeignKey(
#         Drug, on_delete=models.CASCADE,
#         related_name='complements')
#     lote = models.CharField(
#         max_length=80, blank=True, null=True, verbose_name='Lote')
#     expiration_date = models.DateField(
#         blank=True, null=True, verbose_name='Fecha de caducidad')
#     total_price = models.FloatField(blank=True, null=True)
#
#     class Meta:
#         verbose_name = "Insumos"
#         verbose_name_plural = "Insumos (medicamentos)"
#
#     def __str__(self):
#         return str(self.uuid)


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


class MotherDrugLosartan(models.Model):
    from geo.models import CLUES, Delegation, Entity
    from inai.models import EntityWeek
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, db_column="entity_id",
        primary_key=True)
    medical_unit = models.ForeignKey(
        MedicalUnit, on_delete=models.CASCADE, db_column="medical_unit_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.CASCADE, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, db_column="delivered_id")
    prescribed_total = models.IntegerField(db_column="prescribed")
    delivered_total = models.IntegerField(db_column="delivered")
    total = models.IntegerField(db_column="total")

    class Meta:
        managed = False
        db_table = 'mother_drug_losartan'
        verbose_name = "Dato Losartan"
        verbose_name_plural = "Datos Losartan"

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.entity, self.medical_unit, self.entity_week, self.delivered)


# -- TABLE mother_drug_priority
# SELECT med_unit.delegation_id,
#    med_unit.clues_id,
#    drug.entity_week_id,
#    drug.delivered_id,
#    cont.key,
#    cont.id AS container_id,
#    sum(drug.prescribed_amount) AS prescribed,
#    sum(drug.delivered_amount) AS delivered,
#    count(*) AS total
#   FROM formula_rx rx
#     JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id::text = med_unit.hex_hash::text
#     JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
#     JOIN med_cat_medicament med_cat ON drug.medicament_id::text = med_cat.hex_hash::text
#     JOIN medicine_container cont ON cont.id = med_cat.container_id
#     JOIN medicine_presentation pres ON pres.id = cont.presentation_id
#     JOIN medicine_component comp ON comp.id = pres.component_id
#  WHERE comp.priority < 4
#  GROUP BY med_unit.delegation_id, med_unit.clues_id, drug.entity_week_id, drug.delivered_id, cont.key, cont.id;


class MotherDrugPriority(models.Model):
    from geo.models import CLUES, Delegation, Entity
    from inai.models import EntityWeek
    from medicine.models import Container
    key = models.CharField(max_length=255, primary_key=True, db_column="key")
    clues = models.ForeignKey(
        CLUES, on_delete=models.CASCADE, db_column="clues_id")
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, db_column="delegation_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.CASCADE, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, db_column="delivered_id")
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, db_column="container_id")
    prescribed_total = models.IntegerField(db_column="prescribed")
    delivered_total = models.IntegerField(db_column="delivered")
    total = models.IntegerField(db_column="total")

    class Meta:
        managed = False
        db_table = 'mother_drug_priority'
        verbose_name = "Dato Prioridad"
        verbose_name_plural = "Datos Prioridad"

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.entity_week, self.delivered, self.container, self.key)

# SELECT med_unit.delegation_id,
#    med_unit.clues_id,
#    drug.entity_week_id,
#    drug.delivered_id,
#    sum(drug.prescribed_amount) AS prescribed,
#    sum(drug.delivered_amount) AS delivered,
#    count(*) AS total
#   FROM formula_rx rx
#     JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id::text = med_unit.hex_hash::text
#     JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
#  GROUP BY med_unit.delegation_id, med_unit.clues_id, drug.entity_week_id, drug.delivered_id;


class MotherDrugTotals(models.Model):
    from geo.models import CLUES, Delegation, Entity
    from inai.models import EntityWeek
    clues = models.ForeignKey(
        CLUES, on_delete=models.CASCADE, db_column="clues_id")
    delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, db_column="delegation_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.CASCADE, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.CASCADE, db_column="delivered_id")
    prescribed_total = models.IntegerField(db_column="prescribed")
    delivered_total = models.IntegerField(db_column="delivered")
    total = models.IntegerField(db_column="total", primary_key=True)

    class Meta:
        managed = False
        db_table = 'mother_drug_totals'
        verbose_name = "Dato Total"
        verbose_name_plural = "Datos Totales"

    def __str__(self):
        return "%s -- %s -- %s" % (
            self.entity_week, self.delivered, self.clues)
