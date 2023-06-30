from django.db import models
from django.db.models import JSONField

from geo.models import Agency, Entity
from category.models import (
    StatusControl, FileType, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat)
from classify_task.models import Stage, StatusTask
from transparency.models import Anomaly
from data_param.models import (
    DataType, FinalField, CleanFunction,
    DataGroup, Collection, ParameterGroup, FileControl)

from .data_file_mixins.explore_mix import ExploreMix
from .data_file_mixins.utils_mix import DataUtilsMix
from .data_file_mixins.get_data_mix import ExtractorsMix
# from .data_file_mixins.matches_mix import MatchesMix
from .reply_file_mixins.process_mix import ReplyFileMix

from .petition_mixins.petition_mix import PetitionTransformsMix


def set_upload_path_old(instance, filename):
    # from django.conf import settings
    # files_path = getattr(settings, "FILES_PATH")
    is_sheet_file = getattr(instance, "data_file", False)
    if is_sheet_file:
        instance = instance.data_file
    try:
        petition = instance.petition_file_control.petition
    except AttributeError:
        try:
            petition = instance.petition
        except AttributeError:
            return "/".join(["sin_instance", filename])

    agency_type = petition.agency.agency_type[:8].lower()
    try:
        acronym = petition.agency.acronym.lower()
    except AttributeError:
        acronym = 'others'
    try:
        last_year_month = instance.entity_month.year_month
    except AttributeError:
        try:
            last_year_month = petition.last_year_month()
        except IndexError:
            last_year_month = "others"
    except Exception as e:
        print(e)
        last_year_month = "others"
    # final_path = "/".join([agency_type, acronym, last_year_month, filename])
    # print(os.path.join('/media/%s/' % instance.id, filename))
    # print(os.path.join(files_path, final_path))
    return "/".join([agency_type, acronym, last_year_month, filename])


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
            return "/".join(["sin_instance", filename])

    agency_type = petition.agency.agency_type[:8].lower()
    try:
        acronym = petition.agency.acronym.lower()
    except AttributeError:
        acronym = 'others'
    folio_petition = petition.folio_petition
    elems = [agency_type, acronym, folio_petition, filename]
    if settings.IS_LOCAL:
        elems.insert(3, "localhost")

    return "/".join([agency_type, acronym, folio_petition, filename])


class Petition(models.Model, PetitionTransformsMix):

    folio_petition = models.CharField(
        max_length=50,
        verbose_name="Folio de la solicitud")
    agency = models.ForeignKey(
        Agency,
        related_name="petitions",
        on_delete=models.CASCADE)
    real_entity = models.ForeignKey(
        Entity, related_name="real_petitions",
        on_delete=models.CASCADE, null=True, blank=True)
    ask_extension = models.BooleanField(
        blank=True, null=True,
        verbose_name="Se solicitó extensión")
    notes = models.TextField(blank=True, null=True)
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
    description_complain = models.TextField(
        verbose_name="Texto de la queja",
        blank=True, null=True)
    status_data = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_data",
        verbose_name="Status de los datos entregados",
        on_delete=models.CASCADE)
    status_petition = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_petition",
        verbose_name="Status de la petición",
        on_delete=models.CASCADE)
    status_complain = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_complain",
        verbose_name="Status de la queja",
        on_delete=models.CASCADE)
    invalid_reason = models.ForeignKey(
        InvalidReason, null=True, blank=True,
        verbose_name="Razón de invalidez",
        on_delete=models.CASCADE)
    folio_complain = models.IntegerField(
        verbose_name="Folio de la queja",
        blank=True, null=True)
    id_inai_open_data = models.IntegerField(
        verbose_name="Id en el sistema de INAI",
        blank=True, null=True)
    info_queja_inai = JSONField(
        verbose_name="Datos de queja",
        help_text="Información de la queja en INAI Search",
        blank=True, null=True)
    entity_months = models.ManyToManyField(
        "EntityMonth", blank=True, verbose_name="Meses de la solicitud")

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__petition=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def first_year_month(self):
        # return self.petition_months.earliest().entity_month.year_month
        if self.entity_months.exists():
            return self.entity_months.earliest().year_month
        return None

    def last_year_month(self):
        # return self.petition_months.latest().entity_month.year_month
        if self.entity_months.exists():
            return self.entity_months.latest().year_month
        return None

    def months(self):
        html_list = ''
        # start = self.petition_months.earliest().entity_month.human_name
        start = self.entity_months.earliest().year_month
        # end = self.petition_months.latest().entity_month.human_name
        end = self.entity_months.latest().year_month
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
        return "%s -- %s" % (self.agency, self.folio_petition or self.id)

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


class EntityMonth(models.Model):
    agency = models.ForeignKey(
        Agency,
        verbose_name="Sujeto Obligado",
        related_name="months",
        on_delete=models.CASCADE, blank=True, null=True)
    entity = models.ForeignKey(
        Entity,
        related_name="entity_months",
        verbose_name="Proveedor de servicios de salud",
        on_delete=models.CASCADE, blank=True, null=True)
    year_month = models.CharField(max_length=10)
    drugs_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    last_transformation = models.DateTimeField(blank=True, null=True)
    last_crossing = models.DateTimeField(blank=True, null=True)
    last_merge = models.DateTimeField(blank=True, null=True)
    last_insertion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.entity.acronym, self.year_month)

    @property
    def human_name(self):
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        year, month = self.year_month.split("-")
        month_name = months[int(month)-1]
        return "%s/%s" % (month_name, year)

    class Meta:
        get_latest_by = "year_month"
        ordering = ["year_month"]
        verbose_name = "Mes de entidad"
        verbose_name_plural = "Meses de entidad"


class PetitionMonth(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="petition_months",
        on_delete=models.CASCADE)
    entity_month = models.ForeignKey(EntityMonth, on_delete=models.CASCADE)

    def __str__(self):
        return "%s-> %s, %s" % (self.id, self.petition, self.entity_month)

    class Meta:
        get_latest_by = "month_agency__year_month"
        verbose_name = "Mes de solicitud"
        verbose_name_plural = "Meses de solicitud"


def default_explore_data():
    return {}


class ReplyFile(models.Model, ReplyFileMix):

    petition = models.ForeignKey(
        Petition,
        related_name="reply_files",
        on_delete=models.CASCADE)
    file = models.FileField(
        verbose_name="archivo",
        max_length=150, upload_to=set_upload_path,
        blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    file_type = models.ForeignKey(
        FileType, on_delete=models.CASCADE,
        default='no_final_info', blank=True, null=True)
    text = models.TextField(
        blank=True, null=True,
        verbose_name="Texto (en caso de no haber archivo)")
    url_download = models.URLField(
        max_length=400, blank=True, null=True,
        verbose_name="Url donde se puede descargar el archivo")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")
    addl_params = JSONField(
        blank=True, null=True, verbose_name="Otras configuraciones")
    has_data = models.BooleanField(
        default=False, verbose_name="Contiene los datos")

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__reply_file=self, inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    def __str__(self):
        first = (self.file or (self.text and self.text[:80])
                 or self.url_download or 'None')
        return "%s -- %s" % (first, self.petition)

    class Meta:
        verbose_name = "Archivo sin datos finales"
        verbose_name_plural = "2. Archivos sin datos finales"


class DataFile(models.Model, ExploreMix, DataUtilsMix, ExtractorsMix):

    file = models.FileField(max_length=150, upload_to=set_upload_path)
    entity = models.ForeignKey(
        Entity, related_name="data_files", on_delete=models.CASCADE,
        blank=True, null=True)
    zip_path = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    # petition_month = models.ForeignKey(
    #     PetitionMonth, blank=True, null=True,
    #     on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    # is_final = models.BooleanField(default= True)
    # origin_file = models.ForeignKey(
    #     "DataFile", blank=True, null=True, related_name="child_files",
    #     verbose_name="archivo origen", on_delete=models.CASCADE)
    reply_file = models.ForeignKey(
        ReplyFile, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="archivo base", related_name="data_file_childs")
    petition_file_control = models.ForeignKey(
        PetitionFileControl, related_name="data_files", blank=True, null=True,
        on_delete=models.CASCADE)
    status_process = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE)

    stage = models.ForeignKey(
        Stage, blank=True, null=True, on_delete=models.CASCADE,
        default='initial', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, blank=True, null=True, on_delete=models.CASCADE,
        default='finished', verbose_name="Status actual")

    # file_type = models.ForeignKey(
    #     FileType, blank=True, null=True, on_delete=models.CASCADE,
    #     default='original_data',
    #     verbose_name="Tipo de archivo")

    filtered_sheets = JSONField(
        blank=True, null=True, verbose_name="Nombres de las hojas filtradas")
    suffix = models.CharField(
        max_length=10, blank=True, null=True)
    directory = models.CharField(
        max_length=255, verbose_name="Ruta en archivo comprimido",
        blank=True, null=True)
    error_process = JSONField(
        blank=True, null=True, verbose_name="Errores de procesamiento")
    warnings = JSONField(
        blank=True, null=True, verbose_name="Advertencias")
    total_rows = models.IntegerField(default=0)
    # Creo que deben eliminarse:
    sample_data = JSONField(
        blank=True, null=True, verbose_name="Primeros datos, de exploración")
    sheet_names = JSONField(
        blank=True, null=True, verbose_name="Nombres de las hojas")
    # {"all": [], "filtered": [], "matched": []}
    all_results = JSONField(
        blank=True, null=True, verbose_name="Todos los resultados")

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file=self, inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    @property
    def sheet_names_list(self):
        return self.sheet_files \
            .filter(file_type_id__in=['sheet', 'split', 'clone']) \
            .order_by("id") \
            .values_list("sheet_name", flat=True)

    @property
    def all_sample_data(self):
        sheet_files = self.sheet_files \
            .filter(file_type_id__in=['sheet', 'split', 'clone'])
        return {tf.sheet_name: tf.sample_data for tf in sheet_files}

    @property
    def last_lap(self):
        from django.db.models import Max
        laps = LapSheet.objects.filter(sheet_file__data_file=self)
        if laps.exists():
            last_sheet = laps.aggregate(Max('lap'))
            return last_sheet['lap__max']
        return -2

    @property
    def next_lap(self):
        lap_number = 0
        last_lap = LapSheet.objects.filter(sheet_file__data_file=self)\
            .order_by("-inserted", "lap").last()
        if last_lap:
            lap_number = last_lap.lap + 1 if last_lap.inserted else last_lap.lap
        return lap_number if lap_number >= 0 else 0

    @property
    def can_repeat(self):
        from datetime import datetime, timedelta
        from django.utils.timezone import make_aware
        if self.status.is_completed:
            return True
        x_minutes = 15
        last_task = self.async_tasks.filter(is_current=True).last()
        if not last_task:
            return True
        if last_task.status_task.is_completed:
            return True
        quick_status = ['success', 'pending', 'created']
        if last_task.status_task in quick_status:
            x_minutes = 2
        now = make_aware(datetime.now())
        last_update = last_task.date_arrive or last_task.date_start
        # more_than_x_minutes = (
        #     now - timedelta(minutes=x_minutes)) > last_update
        more_than_x_minutes = (
            now - last_update) > timedelta(minutes=x_minutes)

        return more_than_x_minutes

    def __str__(self):
        return "%s %s" % (str(self.file), self.petition_file_control)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Archivo con datos"
        verbose_name_plural = "3. Archivos con datos"


class Behavior(models.Model):

    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=80)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=80, blank=True, null=True)
    color = models.CharField(max_length=80, blank=True, null=True)
    is_merge = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Comportamiento"
        verbose_name_plural = "4. Comportamientos Merge"


class SheetFile(models.Model):

    data_file = models.ForeignKey(
        DataFile, related_name="sheet_files", on_delete=models.CASCADE)
    file = models.FileField(max_length=255, upload_to=set_upload_path)
    file_type = models.ForeignKey(
        FileType, on_delete=models.CASCADE, blank=True, null=True)
    matched = models.BooleanField(blank=True, null=True)
    sheet_name = models.CharField(max_length=255, blank=True, null=True)
    sample_data = JSONField(blank=True, null=True, default=default_explore_data)
    total_rows = models.IntegerField(default=0)
    error_process = JSONField(blank=True, null=True)
    warnings = JSONField(blank=True, null=True)
    year_month = models.CharField(
        max_length=8, blank=True, null=True, verbose_name="Año y mes")
    entity_months = models.ManyToManyField(
        EntityMonth, blank=True, related_name="sheet_files")
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='explore', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')
    rx_count = models.IntegerField(
        verbose_name="Prescripciones procesadas",
        default=0)
    duplicates_count = models.IntegerField(
        verbose_name="Duplicados",
        default=0)
    shared_count = models.IntegerField(
        verbose_name="Compartidos",
        default=0)
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, default='pending',
        verbose_name="merge behavior")
    # completed_rows = models.IntegerField(default=0)
    # inserted_rows = models.IntegerField(default=0)
    # all_results = JSONField(blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        some_inserted = self.laps.filter(inserted=True).exists()
        if some_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(using, keep_parents)

    @property
    def next_lap(self):
        lap_number = 0
        last_lap = self.laps.all().order_by("-inserted", "lap").last()
        if last_lap:
            lap_number = last_lap.lap + 1 if last_lap.inserted else last_lap.lap
        return lap_number if lap_number >= 0 else 0

    def save_stage(self, status_id, errors):
        self.stage_id = status_id
        if errors:
            self.status_id = "with_errors"
            self.error_process = errors
        else:
            self.status_id = "finished"
            self.error_process = []
        self.save()
        self.data_file.comprobate_sheets(status_id)

    def __str__(self):
        return f">{self.file_type}< {self.sheet_name}- {self.data_file}"

    class Meta:
        verbose_name = "Archivo de pestaña (csv)"
        verbose_name_plural = "4. Archivos de pestaña (Sheets .csv)"
        ordering = ["id"]
        unique_together = ("data_file", "sheet_name", "file_type")


class CrossingSheet(models.Model):
    # entity = models.ForeignKey(
    #     Entity, related_name="crossing_sheets", on_delete=models.CASCADE)
    sheet_file_1 = models.ForeignKey(
        SheetFile, related_name="crossing_1", on_delete=models.CASCADE)
    sheet_file_2 = models.ForeignKey(
        SheetFile, related_name="crossing_2", on_delete=models.CASCADE)
    entity_week = models.ForeignKey(
        "EntityWeek", related_name="crossing_sheets",
        on_delete=models.CASCADE, blank=True, null=True)
    entity_month = models.ForeignKey(
        EntityMonth, related_name="crossing_sheets",
        on_delete=models.CASCADE, blank=True, null=True)
    # year_week = models.CharField(max_length=8, blank=True, null=True)
    # iso_year = models.PositiveIntegerField(default=0)
    # iso_week = models.PositiveIntegerField(default=0)
    # iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    last_crossing = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.sheet_file_1} - {self.sheet_file_2}"

    class Meta:
        get_latest_by = "month_agency__year_month"
        verbose_name = "Mes de cruce"
        verbose_name_plural = "Meses de cruce"


class LapSheet(models.Model):

    sheet_file = models.ForeignKey(
        SheetFile, related_name="laps", on_delete=models.CASCADE)
    lap = models.IntegerField(default=0)
    last_edit = models.DateTimeField(blank=True, null=True)
    inserted = models.BooleanField(default=False, blank=True, null=True)
    cat_inserted = models.BooleanField(default=False, blank=True, null=True)
    missing_inserted = models.BooleanField(default=False, blank=True, null=True)

    general_error = models.CharField(max_length=255, blank=True, null=True)
    total_count = models.IntegerField(default=0)
    processed_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    drug_count = models.IntegerField(default=0)
    medical_unit_count = models.IntegerField(default=0)
    area_count = models.IntegerField(default=0)
    doctor_count = models.IntegerField(default=0)
    diagnosis_count = models.IntegerField(default=0)
    medicament_count = models.IntegerField(default=0)
    discarded_count = models.IntegerField(default=0)
    missing_rows = models.IntegerField(default=0)
    real_missing_rows = models.IntegerField(default=0)
    missing_fields = models.IntegerField(default=0)
    row_errors = JSONField(blank=True, null=True)
    field_errors = JSONField(blank=True, null=True)
    valid_insert = models.BooleanField(default=True)

    def delete(self, using=None, keep_parents=False):
        if self.inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (str(self.sheet_file), self.lap)

    class Meta:
        verbose_name = "Lap de archivo csv"
        verbose_name_plural = "5. Laps de archivo csv"
        ordering = ["id"]
        unique_together = ("sheet_file", "lap")


class EntityWeek(models.Model):
    entity = models.ForeignKey(
        Entity,
        related_name="weeks",
        on_delete=models.CASCADE, blank=True, null=True)
    entity_month = models.ForeignKey(
        EntityMonth,
        related_name="weeks",
        on_delete=models.CASCADE, blank=True, null=True)
    year_week = models.CharField(max_length=8, blank=True, null=True)
    iso_year = models.SmallIntegerField(blank=True, null=True)
    iso_week = models.SmallIntegerField(blank=True, null=True)
    iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    year_month = models.CharField(max_length=10, blank=True, null=True)
    year = models.SmallIntegerField(blank=True, null=True)
    month = models.SmallIntegerField(blank=True, null=True)

    drugs_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)

    last_crossing = models.DateTimeField(blank=True, null=True)
    last_transformation = models.DateTimeField(blank=True, null=True)
    last_merge = models.DateTimeField(blank=True, null=True)
    last_insertion = models.DateTimeField(blank=True, null=True)

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

    def __str__(self):
        return f"{self.entity} {self.year_month} - {self.iso_week} - {self.iso_delegation}"

    class Meta:
        get_latest_by = ["year_month", "year_week"]
        unique_together = (
            "entity", "year_week", "iso_delegation", "year_month")
        verbose_name = "Semana de entidad"
        verbose_name_plural = "7. Semanas de entidad"


class TableFile(models.Model):

    # sheet_file = models.ForeignKey(
    #     SheetFile, related_name="process_files", on_delete=models.CASCADE)
    file = models.FileField(max_length=255, upload_to=set_upload_path)
    lap_sheet = models.ForeignKey(
        LapSheet, related_name="table_files", on_delete=models.CASCADE,
        blank=True, null=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, blank=True, null=True)
    # file_type = models.ForeignKey(
    #     FileType, on_delete=models.CASCADE, blank=True, null=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, blank=True, null=True)
    inserted = models.BooleanField(default=False)

    entity_week = models.ForeignKey(
        EntityWeek, on_delete=models.CASCADE,
        blank=True, null=True, related_name="table_files")
    year_week = models.CharField(max_length=8, blank=True, null=True)
    iso_year = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_week = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    year_month = models.CharField(max_length=8, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    is_for_edition = models.BooleanField(default=False)
    drugs_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)

    def __str__(self):
        return "%s %s" % (self.collection, self.lap_sheet)

    class Meta:
        verbose_name = "Archivo para insertar"
        verbose_name_plural = "6. Archivos para insertar"
        ordering = ["-id"]
        unique_together = (
            "lap_sheet", "collection", "is_for_edition", "year",
            "iso_week", "iso_delegation")
