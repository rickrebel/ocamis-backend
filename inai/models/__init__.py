from django.db import models
from django.db.models import JSONField

from geo.models import Agency, Provider, Delegation
from category.models import (
    ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat, StatusControl)
from classify_task.models import Stage, StatusTask
from transparency.models import Anomaly
from data_param.models import (
    DataType, FinalField, CleanFunction,
    DataGroup, Collection, ParameterGroup, FileControl)
from med_cat.models import Delivered
from .petition import Petition, RequestTemplate
from .month_record import MonthRecord
from rds.models import Cluster


class WeekRecord(models.Model):
    provider = models.ForeignKey(
        Provider,
        related_name="weeks",
        on_delete=models.CASCADE, blank=True, null=True)
    month_record = models.ForeignKey(
        MonthRecord,
        related_name="weeks",
        on_delete=models.CASCADE, blank=True, null=True)
    year_week = models.CharField(max_length=8, blank=True, null=True)
    iso_year = models.SmallIntegerField(blank=True, null=True)
    iso_week = models.SmallIntegerField(blank=True, null=True)
    # iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
    year_month = models.CharField(max_length=10, blank=True, null=True)
    year = models.SmallIntegerField(blank=True, null=True)
    month = models.SmallIntegerField(blank=True, null=True)

    drugs_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    self_repeated_count = models.IntegerField(default=0)
    crosses = JSONField(blank=True, null=True)

    last_crossing = models.DateTimeField(blank=True, null=True)
    last_transformation = models.DateTimeField(blank=True, null=True)
    last_merge = models.DateTimeField(blank=True, null=True)
    last_pre_insertion = models.DateTimeField(blank=True, null=True)

    # PROVISIONAL HARDCODED
    zero = models.IntegerField(blank=True, null=True)
    unknown = models.IntegerField(blank=True, null=True)
    unavailable = models.IntegerField(blank=True, null=True)
    partial = models.IntegerField(blank=True, null=True)
    over_delivered = models.IntegerField(blank=True, null=True)
    error = models.IntegerField(blank=True, null=True)
    denied = models.IntegerField(blank=True, null=True)
    complete = models.IntegerField(blank=True, null=True)
    cancelled = models.IntegerField(blank=True, null=True)
    big_denied = models.IntegerField(blank=True, null=True)
    big_partial = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.provider} {self.year_month} - {self.iso_week} - {self.iso_delegation}"

    class Meta:
        get_latest_by = ["year_month", "year_week"]
        unique_together = (
            "provider", "year_week", "iso_delegation", "year_month")
        verbose_name = "Semana-proveedor"
        verbose_name_plural = "9. Semanas-proveedores"
        db_table = "inai_entityweek"


VARIABLE_TYPES = (
    ("string", "String"),
    ("provider", "By Provider"),
    # ("name_provider", "Nombre del sujeto obligado"),
    ("date", "Date"),
)


class Variable(models.Model):
    request_template = models.ForeignKey(
        RequestTemplate, related_name="variables",
        on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    variable_type = models.CharField(
        max_length=15, choices=VARIABLE_TYPES, default="string")
    default_value = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name or "Variable"

    class Meta:
        verbose_name = "Variable de plantilla"
        verbose_name_plural = "Variables de plantilla"


class PetitionDataGroup(models.Model):
    petition = models.ForeignKey(
        Petition, related_name="data_groups", on_delete=models.CASCADE)
    data_group = models.ForeignKey(
        DataGroup, related_name="petitions", on_delete=models.CASCADE)
    status_data = models.ForeignKey(
        StatusControl, related_name="petition_data_groups_data",
        on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.petition, self.data_group)

    class Meta:
        verbose_name = "Petición - Grupo de datos (m2m)"
        verbose_name_plural = "Peticiones - Grupos de datos (m2m)"


class Complaint(models.Model):
    petition = models.ForeignKey(
        Petition, related_name="complaints",
        on_delete=models.CASCADE)
    folio_complaint = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Expediente")
    info_queja_inai = JSONField(
        verbose_name="Datos de queja",
        help_text="Información de la queja en INAI Search",
        blank=True, null=True)
    description = models.TextField(
        verbose_name="Texto de la queja",
        blank=True, null=True)
    status_complaint = models.ForeignKey(
        StatusControl, related_name="complaints",
        on_delete=models.CASCADE, blank=True, null=True)
    date_complaint = models.DateField(
        verbose_name="Fecha de envío",
        blank=True, null=True)
    relevant_data = JSONField(
        verbose_name="Datos relevantes",
        help_text="Datos relevantes de la queja",
        blank=True, null=True)

    def save_json_data(self, data):
        from scripts.import_inai import date_mex
        from category.models import StatusControl
        self.info_queja_inai = data
        description = data.get("ACTO_RECURRIDO", "")
        if description:
            self.description = description
        date_complaint = data.get("FECHA_OFICIAL")
        if date_complaint:
            self.date_complaint = date_mex(date_complaint)
        status_name = data.get("SENTIDO_RESOLUCION")
        if status_name:
            status_lower = status_name.lower()
            try:
                status_complaint = StatusControl.objects.get(
                    name=status_lower, group="complain")
            except StatusControl.DoesNotExist:
                description_status = f"Nombre oficial: {status_name}"
                status_complaint = StatusControl.objects.create(
                    name=status_lower,
                    public_name=status_name,
                    official_name=status_name,
                    description=description_status,
                    color="pink accent-4",
                    group="complain")
            self.status_complaint = status_complaint
        irrelevant_fields = [
            "EXPEDIENTE", "FECHA_OFICIAL", "FOLIO_SOLICITUD", "SUJETO_OBLIGADO",
            "ID_ORGANO_GARANTE", "ID_MEDIO_IMPUGNACION", "SENTIDO_RESOLUCION",
            "TIPO_MEDIO_IMPUGNACION", "ACTO_RECURRIDO", "ID_SUJETO_OBLIGADO"]
        relevant_data = {}
        for key, value in data.items():
            if value and key not in irrelevant_fields:
                relevant_data[key] = value
        self.relevant_data = relevant_data
        self.save()

    def __str__(self):
        return f"{self.folio_complaint} - {self.petition}"

    class Meta:
        verbose_name = "Queja"
        verbose_name_plural = "2. Quejas"


class PetitionBreak(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="break_dates",
        on_delete=models.CASCADE)
    date_break = models.ForeignKey(
        DateBreak, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return "%s, %s" % (self.petition, self.date_break)

    class Meta:
        verbose_name = "Petición - fecha de corte (m2m)"
        verbose_name_plural = "Peticiones - fechas de corte (m2m)"


class PetitionNegativeReason(models.Model):
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE,
        related_name="negative_reasons",)
    negative_reason = models.ForeignKey(
        NegativeReason, on_delete=models.CASCADE)
    is_main = models.BooleanField(
        verbose_name="Es la razón principal")

    def __str__(self):
        return "%s, %s" % (self.petition, self.negative_reason)

    class Meta:
        verbose_name = "Petición - razón negativa (m2m)"
        verbose_name_plural = "Peticiones - razones negativas (m2m)"


class VariableValue(models.Model):
    variable = models.ForeignKey(
        Variable, related_name="values",
        on_delete=models.CASCADE)
    provider = models.ForeignKey(
        Provider, related_name="variable_values",
        on_delete=models.CASCADE, blank=True, null=True)
    petition = models.ForeignKey(
        Petition, related_name="variable_values",
        on_delete=models.CASCADE, blank=True, null=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Valor de variable"
        verbose_name_plural = "Valores de variable"


class PetitionFileControl(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="file_controls",
        on_delete=models.CASCADE)
    # file_control = models.IntegerField(blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, on_delete=models.CASCADE,
        related_name="petition_file_control",)

    def save(self, *args, **kwargs):
        print("PetitionFileControl.save")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from respond.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception(
                "No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def __str__(self):
        return "%s - %s" % (self.petition, self.file_control)

    class Meta:
        unique_together = ("petition", "file_control")
        verbose_name = "Relacional: petición -- Grupo de Control"
        verbose_name_plural = "7. Relacional: Petición -- Grupos de Control"


class DeliveredWeek(models.Model):
    week_record = models.ForeignKey(
        WeekRecord, related_name="deliveries",
        on_delete=models.CASCADE)
    delivered = models.ForeignKey(
        Delivered, related_name="weeks",
        on_delete=models.CASCADE)
    value = models.IntegerField()

    def __str__(self):
        return f"{self.week_record} - {self.delivered} - {self.value}"

    class Meta:
        verbose_name = "Clasificación de entrega por semana"
        verbose_name_plural = "Clasificaciones de entrega por semana"


sql_view_sums_delivered_by_month = """
CREATE VIEW inai_counts_delivered_by_month AS (
    SELECT
        provider.acronym as provider,
        delegation.name as delegation,
        week_record.year_month,
        week_record.year,
        week_record.month,
        SUM(deliveredweek.value) as total_delivered
    FROM inai_deliveredweek deliveredweek
    JOIN inai_entityweek week_record
        ON deliveredweek.week_record_id = week_record.id
    LEFT JOIN geo_delegation delegation
        ON week_record.iso_delegation_id = delegation.id
    JOIN geo_entity provider
        ON week_record.provider_id = provider.id
    GROUP BY week_record.year_month, 
        week_record.year,
        week_record.month,
        delegation.name,
        provider.acronym
);
"""


