from django.db import models
from django.db.models import JSONField

from geo.models import Agency, Provider, Delegation
from category.models import (
    OldStatusControl, FileType, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat, StatusControl)
from classify_task.models import Stage, StatusTask
from transparency.models import Anomaly
from data_param.models import (
    DataType, FinalField, CleanFunction,
    DataGroup, Collection, ParameterGroup, FileControl)

# from .data_file_mixins.matches_mix import MatchesMix

from .petition_mixins.petition_mix import PetitionTransformsMix


def set_upload_path(instance, filename):
    from django.conf import settings
    is_sheet_file = getattr(instance, "data_file", False)
    if is_sheet_file:
        instance = instance.data_file
    try:
        petition = instance.petition_file_control.petition
    except AttributeError:
        try:
            petition = instance.petition
        except AttributeError:
            elems = ["sin_instance", filename]
            if settings.IS_LOCAL:
                elems.insert(1, "localhost")
            return "/".join(elems)

    agency_type = petition.agency.agency_type[:8].lower()
    try:
        acronym = petition.agency.acronym.lower()
    except AttributeError:
        acronym = 'others'
    folio_petition = petition.folio_petition
    elems = [agency_type, acronym, folio_petition]
    if settings.IS_LOCAL:
        elems.append("localhost")
    if reply_file := getattr(instance, "reply_file", False):
        elems.append(f"reply_file_{reply_file.id}")
        if instance.directory:
            elems += instance.directory.split("/")
    elems.append(filename)

    return "/".join([agency_type, acronym, folio_petition, filename])


class MonthRecord(models.Model):
    agency = models.ForeignKey(
        Agency,
        verbose_name="Sujeto Obligado",
        related_name="months",
        on_delete=models.CASCADE, blank=True, null=True)
    provider = models.ForeignKey(
        Provider,
        related_name="month_records",
        verbose_name="Proveedor de servicios de salud",
        on_delete=models.CASCADE, blank=True, null=True)
    year_month = models.CharField(max_length=10)
    year = models.SmallIntegerField(blank=True, null=True)
    month = models.SmallIntegerField(blank=True, null=True)
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='init_month', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')
    error_process = JSONField(blank=True, null=True)

    drugs_count = models.IntegerField(default=0)
    drugs_in_pre_insertion = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    last_transformation = models.DateTimeField(blank=True, null=True)
    last_crossing = models.DateTimeField(blank=True, null=True)
    last_merge = models.DateTimeField(blank=True, null=True)
    last_pre_insertion = models.DateTimeField(blank=True, null=True)
    last_validate = models.DateTimeField(blank=True, null=True)
    last_indexing = models.DateTimeField(blank=True, null=True)
    last_insertion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.provider.acronym, self.year_month)

    def end_stage(self, stage_id, parent_task):
        child_task_errors = parent_task.child_tasks.filter(
            status_task__macro_status="with_errors")
        all_errors = []
        for child_task_error in child_task_errors:
            current_errors = child_task_error.errors
            if not current_errors:
                g_children = child_task_error.child_tasks.filter(
                    status_task__macro_status="with_errors")
                for g_child in g_children:
                    if g_child:
                        current_errors += g_child.errors or []
            all_errors += current_errors or []
        self.stage_id = stage_id
        if child_task_errors.exists():
            self.status_id = "with_errors"
            self.error_process = all_errors
        else:
            self.status_id = "finished"
            self.error_process = []
        self.save()
        return all_errors

    def save_stage(self, stage_id, errors):
        self.stage_id = stage_id
        if errors:
            self.status_id = "with_errors"
            self.error_process = errors
        else:
            self.status_id = "finished"
            self.error_process = []
        self.save()

    @property
    def human_name(self):
        months = [
            "ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic"]
        year, month = self.year_month.split("-")
        month_name = months[int(month)-1]
        return "%s/%s" % (month_name, year)

    @property
    def temp_table(self):
        year_month = self.year_month.replace("-", "")
        return f"{self.provider_id}_{year_month}"

    class Meta:
        get_latest_by = "year_month"
        db_table = "inai_entitymonth"
        ordering = ["year_month"]
        verbose_name = "8. Mes-proveedor"
        verbose_name_plural = "8. Meses-proveedores"


class RequestTemplate(models.Model):
    version = models.IntegerField()
    version_name = models.CharField(max_length=100, blank=True, null=True)
    text = models.TextField()
    provider = models.ForeignKey(
        Provider, related_name="request_templates",
        verbose_name="Proveedor",
        on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.version_name or str(self.version)

    def save(self, *args, **kwargs):
        if not self.version_name:
            self.version_name = f"Versión {self.version}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Plantilla de solicitud"
        verbose_name_plural = "CAT. Plantillas de solicitud"
        ordering = ["-id"]


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


class Petition(models.Model, PetitionTransformsMix):

    folio_petition = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Folio de la solicitud")
    id_inai_open_data = models.IntegerField(
        verbose_name="Id en el sistema de INAI",
        blank=True, null=True)
    agency = models.ForeignKey(
        Agency, related_name="petitions",
        on_delete=models.CASCADE)
    real_provider = models.ForeignKey(
        Provider, related_name="real_petitions",
        on_delete=models.CASCADE, null=True, blank=True)
    month_records = models.ManyToManyField(
        MonthRecord, blank=True, verbose_name="Meses de la solicitud")
    months_verified = models.BooleanField(
        verbose_name="Meses verificados", default=False)
    notes = models.TextField(blank=True, null=True)
    template_text = models.TextField(
        blank=True, null=True, verbose_name="Texto para la plantilla")
    request_template = models.ForeignKey(
        RequestTemplate, related_name="petitions",
        on_delete=models.CASCADE, null=True, blank=True)
    template_variables = JSONField(
        blank=True, null=True, verbose_name="Variables de la plantilla")
    send_petition = models.DateField(
        verbose_name="Fecha de envío o recepción",
        blank=True, null=True)
    send_response = models.DateField(
        verbose_name="Fecha de última respuesta",
        blank=True, null=True)
    description_petition = models.TextField(
        verbose_name="descripción enviada",
        blank=True, null=True)
    description_response = models.TextField(
        verbose_name="Respuesta texto",
        blank=True, null=True)
    status_petition = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_petition",
        verbose_name="Status de la petición",
        on_delete=models.CASCADE)
    # old_status_petition = models.ForeignKey(
    #     OldStatusControl, null=True, blank=True,
    #     related_name="petitions_petition",
    #     verbose_name="Status de la petición",
    #     on_delete=models.CASCADE)
    status_data = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_data",
        verbose_name="Status de los datos entregados",
        on_delete=models.CASCADE)
    status_priority = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_priority",
        verbose_name="Status de prioridad",
        on_delete=models.CASCADE)
    invalid_reason = models.ForeignKey(
        InvalidReason, null=True, blank=True,
        verbose_name="Razón de invalidez",
        on_delete=models.CASCADE)

    # Complain data, needs to be moved to another model
    ask_extension = models.BooleanField(
        blank=True, null=True,
        verbose_name="Se solicitó extensión")
    description_complain = models.TextField(
        verbose_name="Texto de la queja",
        blank=True, null=True)
    status_complain = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_complain",
        verbose_name="Status de la queja",
        on_delete=models.CASCADE)
    # old_status_complain = models.ForeignKey(
    #     OldStatusControl, null=True, blank=True,
    #     related_name="petitions_complain",
    #     verbose_name="Status de la queja",
    #     on_delete=models.CASCADE)
    folio_complain = models.IntegerField(
        verbose_name="Folio de la queja",
        blank=True, null=True)
    info_queja_inai = JSONField(
        verbose_name="Datos de queja",
        help_text="Información de la queja en INAI Search",
        blank=True, null=True)

    def delete(self, *args, **kwargs):
        from respond.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__petition=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def first_year_month(self):
        # return self.petition_months.earliest().month_record.year_month
        if self.month_records.exists():
            return self.month_records.earliest().year_month
        return None

    def last_year_month(self):
        # return self.petition_months.latest().month_record.year_month
        if self.month_records.exists():
            return self.month_records.latest().year_month
        return None

    @property
    def orphan_pet_control(self):
        orphan_group = DataGroup.objects.get(name="orphan")
        orphan = self.file_controls\
            .filter(file_control__data_group=orphan_group)\
            .first()
        if not orphan:
            name_control = "Archivos por agrupar. Solicitud %s" % (
                self.folio_petition)
            file_control, created = FileControl.objects.get_or_create(
                name=name_control,
                data_group=orphan_group,
                final_data=False,
                agency=self.agency,
            )
            orphan, _ = PetitionFileControl.objects.get_or_create(
                petition=self, file_control=file_control)
        return orphan

    def months(self):
        # html_list = ''
        # start = self.petition_months.earliest().month_record.human_name
        start = self.month_records.earliest().year_month
        # end = self.petition_months.latest().month_record.human_name
        end = self.month_records.latest().year_month
        return " ".join(list({start, end}))
    months.short_description = "Meses"

    def months_in_description(self):
        from django.utils.html import format_html
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        curr_months = []
        if self.description_petition:
            description = self.description_petition.lower()
            for month in months:
                if month in description:
                    curr_months.append(month)
            html_list = ''
            for month in list(curr_months):
                html_list = html_list + ('<span>%s</span><br>' % month)
            return format_html(html_list)
        else:
            return "Sin descripción"
    months_in_description.short_description = "Meses escritos"

    def __str__(self):
        return "solicitud"
        # return "%s -- %s" % (self.agency, self.folio_petition or self.id)

    class Meta:
        verbose_name = "Solicitud - Petición"
        verbose_name_plural = "1. Solicitudes (Peticiones)"


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


class PetitionFileControl(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="file_controls",
        on_delete=models.CASCADE)
    # file_control = models.IntegerField(blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, on_delete=models.CASCADE,
        related_name="petition_file_control",)

    def delete(self, *args, **kwargs):
        from respond.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def __str__(self):
        return "%s - %s" % (self.petition, self.file_control)

    class Meta:
        verbose_name = "Relacional: petición -- Grupo de Control"
        verbose_name_plural = "7. Relacional: Petición -- Grupos de Control"


class PetitionMonth(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="petition_months",
        on_delete=models.CASCADE)
    month_record = models.ForeignKey(MonthRecord, on_delete=models.CASCADE)

    def __str__(self):
        return "%s-> %s, %s" % (self.id, self.petition, self.month_record)

    class Meta:
        get_latest_by = "month_agency__year_month"
        verbose_name = "Mes de solicitud"
        verbose_name_plural = "Meses de solicitud"


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
