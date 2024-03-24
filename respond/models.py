from django.db import models
from django.db.models import JSONField

from category.models import FileType, StatusControl
from classify_task.models import Stage, StatusTask
from data_param.models import Collection
from geo.models import Entity, Delegation
from inai.data_file_mixins.explore_mix import ExploreMix
from inai.data_file_mixins.get_data_mix import ExtractorsMix
from inai.data_file_mixins.utils_mix import DataUtilsMix
from inai.models import Petition, set_upload_path, PetitionFileControl, EntityMonth, EntityWeek
from inai.reply_file_mixins.process_mix import ReplyFileMix


# Create your models here.
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
        db_table = "inai_replyfile"


class DataFile(models.Model, ExploreMix, DataUtilsMix, ExtractorsMix):

    file = models.FileField(max_length=150, upload_to=set_upload_path)
    entity = models.ForeignKey(
        Entity, related_name="data_files", on_delete=models.CASCADE,
        blank=True, null=True)
    # zip_path = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    # petition_month = models.ForeignKey(
    #     PetitionMonth, blank=True, null=True,
    #     on_delete=models.CASCADE)
    # notes = models.TextField(blank=True, null=True)
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

    suffix = models.CharField(
        max_length=10, blank=True, null=True)
    directory = models.CharField(
        max_length=255, verbose_name="Ruta en archivo comprimido",
        blank=True, null=True)
    total_rows = models.IntegerField(default=0)
    sheet_names = JSONField(
        blank=True, null=True, verbose_name="Nombres de las hojas")
    filtered_sheets = JSONField(
        blank=True, null=True, verbose_name="Nombres de las hojas filtradas")
    # {"all": [], "filtered": [], "matched": []}
    error_process = JSONField(
        blank=True, null=True, verbose_name="Errores de procesamiento")
    warnings = JSONField(
        blank=True, null=True, verbose_name="Advertencias")
    sample_data = JSONField(
        blank=True, null=True, verbose_name="Primeros datos, de exploración")
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
        verbose_name_plural = "3. Archivos con datos (DataFile)"
        db_table = "inai_datafile"


class Behavior(models.Model):

    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=80)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=80, blank=True, null=True)
    color = models.CharField(max_length=80, blank=True, null=True)
    is_merge = models.BooleanField(default=False)
    is_discarded = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Comportamiento Merge"
        verbose_name_plural = "CAT. Comportamientos Merge"
        db_table = "inai_behavior"


def default_explore_data():
    return {}


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

    @property
    def filename(self):
        return str(self.file)

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
        db_table = "inai_sheetfile"


class CrossingSheet(models.Model):
    # entity = models.ForeignKey(
    #     Entity, related_name="crossing_sheets", on_delete=models.CASCADE)
    sheet_file_1 = models.ForeignKey(
        SheetFile, related_name="crossing_1", on_delete=models.CASCADE)
    sheet_file_2 = models.ForeignKey(
        SheetFile, related_name="crossing_2", on_delete=models.CASCADE)
    entity_week = models.ForeignKey(
        EntityWeek, related_name="crossing_sheets",
        on_delete=models.CASCADE, blank=True, null=True)
    entity_month = models.ForeignKey(
        EntityMonth, related_name="crossing_sheets",
        on_delete=models.CASCADE, blank=True, null=True)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    last_crossing = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.sheet_file_1} - {self.sheet_file_2}"

    class Meta:
        get_latest_by = "month_agency__year_month"
        verbose_name = "Cruce de archivos"
        verbose_name_plural = "5.1 Cruces de archivos"
        db_table = "inai_crossingsheet"


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
    drugs_count = models.IntegerField(default=0)
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
        db_table = "inai_lapsheet"


class TableFile(models.Model):

    # sheet_file = models.ForeignKey(
    #     SheetFile, related_name="process_files", on_delete=models.CASCADE)
    file = models.FileField(max_length=255, upload_to=set_upload_path)
    lap_sheet = models.ForeignKey(
        LapSheet, related_name="table_files", on_delete=models.CASCADE,
        blank=True, null=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, blank=True, null=True,
        related_name="table_files")
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
    # iso_delegation = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
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

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    class Meta:
        verbose_name = "Archivo para insertar"
        verbose_name_plural = "6. Archivos para insertar"
        ordering = ["-id"]
        unique_together = (
            "lap_sheet", "collection", "is_for_edition", "year",
            "iso_week", "iso_delegation")
        db_table = "inai_tablefile"
