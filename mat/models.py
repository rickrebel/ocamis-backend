from django.db import models
from django.conf import settings
from med_cat.models import MedicalUnit, Delivered
is_big_active = getattr(settings, "IS_BIG_ACTIVE")
is_managed = not is_big_active


class MotherDrugPriority(models.Model):
    from geo.models import CLUES, Delegation, Provider
    from inai.models import EntityWeek
    from medicine.models import Container
    delegation = models.ForeignKey(
        Delegation, on_delete=models.DO_NOTHING, db_column="delegation_id")
    clues = models.ForeignKey(
        CLUES, on_delete=models.DO_NOTHING, db_column="clues_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.DO_NOTHING, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.DO_NOTHING, db_column="delivered_id")
    key = models.CharField(max_length=255, primary_key=True, db_column="key")
    container = models.ForeignKey(
        Container, on_delete=models.DO_NOTHING, db_column="container_id")
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


class MotherDrug(models.Model):
    from geo.models import CLUES, Delegation, Provider
    from inai.models import EntityWeek
    from medicine.models import Container
    key = models.CharField(max_length=255, primary_key=True, db_column="key")
    clues = models.ForeignKey(
        CLUES, on_delete=models.DO_NOTHING, db_column="clues_id")
    delegation = models.ForeignKey(
        Delegation, on_delete=models.DO_NOTHING, db_column="delegation_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.DO_NOTHING, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.DO_NOTHING, db_column="delivered_id")
    container = models.ForeignKey(
        Container, on_delete=models.DO_NOTHING, db_column="container_id")
    prescribed_total = models.IntegerField(db_column="prescribed")
    delivered_total = models.IntegerField(db_column="delivered")
    total = models.IntegerField(db_column="total")

    class Meta:
        managed = False
        db_table = 'mother_drug'
        verbose_name = "Tabla Madre. Drugs"
        verbose_name_plural = "Tabla Madre. Drugs"

    def __str__(self):
        return "%s -- %s -- %s -- %s" % (
            self.entity_week, self.delivered, self.container, self.key)


# class MotherDrugExtended(models.Model):
#     from geo.models import Delegation, Provider
#     from inai.models import EntityWeek
#     from medicine.models import Component, Presentation, Container
#     delegation = models.ForeignKey(
#         Delegation, on_delete=models.DO_NOTHING, db_column="delegation_id")
#     iso_year = models.PositiveSmallIntegerField(db_column="iso_year")
#     iso_week = models.PositiveSmallIntegerField(db_column="iso_week")
#     provider = models.ForeignKey(
#         Provider, on_delete=models.DO_NOTHING, db_column="entity_id")
#     component = models.ForeignKey(
#         Component, on_delete=models.DO_NOTHING, db_column="component_id")
#     presentation = models.ForeignKey(
#         Presentation, on_delete=models.DO_NOTHING, db_column="presentation_id")
#     container = models.ForeignKey(
#         Container, on_delete=models.DO_NOTHING, db_column="container_id")
#     prescribed_total = models.IntegerField(db_column="prescribed")
#     delivered_total = models.IntegerField(db_column="delivered")
#     total = models.IntegerField(db_column="total", primary_key=True)
#
#     class Meta:
#         managed = False
#         db_table = 'mother_drug_extended'
#         verbose_name = "Dato Extendido"
#         verbose_name_plural = "Datos Extendidos"
#
#     def __str__(self):
#         return "%s -- %s -- %s -- %s" % (
#             self.iso_year, self.iso_week, self.provider, self.component)


class MotherDrugTotals(models.Model):
    from geo.models import CLUES, Delegation, Provider
    from inai.models import EntityWeek
    clues = models.ForeignKey(
        CLUES, on_delete=models.DO_NOTHING, db_column="clues_id")
    delegation = models.ForeignKey(
        Delegation, on_delete=models.DO_NOTHING, db_column="delegation_id")
    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.DO_NOTHING, db_column="entity_week_id")
    delivered = models.ForeignKey(
        Delivered, on_delete=models.DO_NOTHING, db_column="delivered_id")
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
