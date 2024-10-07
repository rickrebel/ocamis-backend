from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from django.db import models
from django.db.models import JSONField

from category.models import FileType
from classify_task.models import Stage, StatusTask
from data_param.models import Collection, FileControl
from geo.models import Provider, Delegation
# from respond.data_file_mixins.explore_mix import ExploreMix
# from respond.data_file_mixins.get_data_mix import ExtractorsMix
from respond.data_file_mixins.utils_mix import DataUtilsMix
from inai.models import (
    Petition, PetitionFileControl, MonthRecord, WeekRecord)

can_delete_s3 = getattr(
    settings, "CAN_DELETE_AWS_STORAGE_FILES", False)


def join_path(elems, filename):
    from django.conf import settings
    if settings.IS_LOCAL:
        elems.insert(0, "localhost")
    elems.append(filename)
    all_together = "/".join(elems)
    folders = all_together.split("/")
    final_directory = []
    for folder in folders:
        if folder not in final_directory:
            final_directory.append(folder)
    return "/".join(final_directory)


def get_elems_by_provider(provider, first_elem=None):
    provider_type = provider.provider_type[:8].lower()
    acronym = provider.acronym.lower()
    elems = [provider_type, acronym]
    if first_elem:
        elems.insert(0, first_elem)
    return elems


def get_path_with_petition(
        pet_obj, filename, first_elem=None, last_elems=None):
    elems = get_elems_by_provider(pet_obj.agency.provider, first_elem)
    elems.append(pet_obj.folio_petition[-8:])
    if last_elems:
        elems += last_elems
    return join_path(elems, filename)


def set_upload_data_file_path(
        data_file, filename, first_elem="data", collection_name=None):
    last_elems = []
    if collection_name:
        last_elems.append(collection_name)
    if reply_file := data_file.reply_file:
        # TODO Future: Esto está repetido en algunos lugares
        last_elems.append(f"rf_{reply_file.id}")
        if data_file.directory:
            last_elems += data_file.directory.split("/")
    pet_obj = data_file.petition_file_control.petition
    return get_path_with_petition(
        pet_obj, filename, first_elem, last_elems=last_elems)


def set_upload_sheet_file_path(sheet_file, filename):
    data_file = sheet_file.data_file
    return set_upload_data_file_path(data_file, filename, "sheet")


def set_upload_table_file_path(table_file, filename):
    collection = table_file.collection
    lap_sheet = table_file.lap_sheet
    first_elem = "table"
    if collection and lap_sheet:
        collection_name = collection.snake_name
    elif not collection and lap_sheet:
        collection_name = "by_week"
    elif collection and not lap_sheet:
        collection_name = collection.snake_name
        first_elem = "merged_tables"
    else:
        raise ValueError("No se puede determinar el tipo de archivo")
    if lap_sheet:
        data_file = lap_sheet.sheet_file.data_file
        return set_upload_data_file_path(
            data_file, filename, first_elem, collection_name)
    elems = get_elems_by_provider(table_file.provider, first_elem)
    elems.append(collection_name)
    elems.append(table_file.week_record.year)
    return join_path(elems, filename)


def set_upload_reply_path(reply_file, filename, first_elem="reply"):
    pet_obj = reply_file.petition
    return get_path_with_petition(pet_obj, filename, first_elem)


class ReplyFile(models.Model):

    petition = models.ForeignKey(
        Petition, related_name="reply_files", on_delete=models.CASCADE)
    file = models.FileField(
        verbose_name="archivo",
        max_length=255, upload_to=set_upload_reply_path,
        blank=True, null=True)
    instant_access = models.BooleanField(
        default=True, verbose_name="Acceso instantáneo")
    available_until = models.DateTimeField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    # file_type = models.ForeignKey(
    #     FileType, on_delete=models.CASCADE,
    #     default='no_final_info', blank=True, null=True)
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
    month_records = models.ManyToManyField(
        MonthRecord, related_name="reply_files", blank=True)

    def save(self, *args, **kwargs):
        if self.pk and can_delete_s3:
            try:
                old_instance = ReplyFile.objects.get(pk=self.pk)
                if old_instance.file and old_instance.file != self.file:
                    old_instance.file.delete(save=False)
            except ReplyFile.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__reply_file=self, inserted=True).exists()
        if some_lap_inserted:
            raise Exception(
                "No se puede eliminar un archivo con datos insertados")

        # if can_delete_s3:
        #     self.file.delete(save=False)
        # else:
        #     print("No se pueden borrar archivos en AWS")

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


# params_glacier_ir = {"object_parameters": {"StorageClass": "GLACIER_IR"}}
params_glacier_ir = {"gzip": True, "object_parameters": {
    "StorageClass": "GLACIER_IR"}}


class DataFile(models.Model, DataUtilsMix):

    file = models.FileField(
        max_length=255, upload_to=set_upload_data_file_path,
        storage=S3Boto3Storage(**params_glacier_ir))
    # file = models.FileField(
    #     max_length=255, upload_to=set_upload_data_file_path)
    provider = models.ForeignKey(
        Provider, related_name="data_files", on_delete=models.CASCADE)
    # zip_path = models.TextField(blank=True, null=True)
    is_duplicated = models.BooleanField(
        blank=True, null=True, verbose_name="Duplicado")
    date = models.DateTimeField(auto_now_add=True)
    reply_file = models.ForeignKey(
        ReplyFile, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="archivo base", related_name="data_file_childs")
    petition_file_control = models.ForeignKey(
        PetitionFileControl, related_name="data_files", blank=True, null=True,
        on_delete=models.CASCADE)

    stage = models.ForeignKey(
        Stage, blank=True, null=True, on_delete=models.CASCADE,
        default='initial', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, blank=True, null=True, on_delete=models.CASCADE,
        default='finished', verbose_name="Status actual")

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
    # Datos de exploración para los archivos .csv
    sample_data = JSONField(
        blank=True, null=True, verbose_name="Primeros datos, de exploración")
    sample_file = models.FileField(
        max_length=255, upload_to=set_upload_data_file_path,
        blank=True, null=True, verbose_name="Archivo con muestra")
    # RICK2 TASK2: TODO: Eliminar este campo
    all_results = JSONField(
        blank=True, null=True, verbose_name="Todos los resultados")
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk and can_delete_s3:
            try:
                old_instance = DataFile.objects.get(pk=self.pk)
                if old_instance.file and old_instance.file != self.file:
                    old_instance.file.delete(save=False)
            except DataFile.DoesNotExist:
                pass
        try:
            super().save(*args, **kwargs)
        except Exception as error:
            print("Error en DataFile.save: ", self.__dict__)

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file=self, inserted=True).exists()
        if some_lap_inserted:
            raise Exception(
                "No se puede eliminar un archivo con datos insertados")

        # if can_delete_s3:
        #     self.file.delete(save=False)
        # else:
        #     print("No se pueden borrar archivos en AWS")

        super().delete(*args, **kwargs)

    def reset_initial(self, pet_file_ctrl=None):
        self.status_id = 'finished'
        self.filtered_sheets = []
        self.warnings = None
        self.error_process = None

        if self.stage_id == 'explore' and not pet_file_ctrl:
            self.stage_id = 'initial'
            self.sheet_files.all().delete()
            self.total_rows = 0
            self.suffix = None
            self.save()
        else:
            self.stage_id = 'explore'
            sheet_files = self.sheet_files.all().values(
                "file", "sheet_name", "file_type",
                "sample_data", "sample_file", "total_rows")
            sheet_files = list(sheet_files)
            if pet_file_ctrl:
                self.pk = None
                self.petition_file_control = pet_file_ctrl
                self.save()
            if not pet_file_ctrl:
                self.sheet_files.all().delete()
            for sheet_file in sheet_files:
                self.sheet_files.create(
                    data_file=self,
                    file=sheet_file["file"],
                    sheet_name=sheet_file["sheet_name"],
                    file_type=sheet_file["file_type"],
                    sample_data=sheet_file["sample_data"],
                    sample_file=sheet_file["sample_file"],
                    total_rows=sheet_file["total_rows"])
        return self

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    @property
    def sheet_names_list(self):
        return self.sheet_files \
            .filter(file_type__in=['sheet', 'split', 'clone']) \
            .order_by("id") \
            .values_list("sheet_name", flat=True)

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

    def stage_ready(self, stage_name="explore"):
        compare_stage = Stage.objects.get(name=stage_name)
        if self.stage.order > compare_stage.order:
            return True
        if self.stage_id == stage_name and self.status_id == "finished":
            return True
        return False

    @property
    def can_repeat(self):
        from datetime import datetime, timedelta
        from django.utils.timezone import make_aware
        if settings.IS_LOCAL:
            return True
        if self.status.is_completed:
            return True

        last_task_incomplete = self.async_tasks\
            .filter(is_current=True)\
            .exclude(status_task__is_completed=True)\
            .last()
        if not last_task_incomplete:
            return True
        quick_status = ['success', 'pending', 'created']
        if last_task_incomplete.status_task in quick_status:
            x_minutes = 2
        else:
            x_minutes = 15
        now = make_aware(datetime.now())
        last_update = (last_task_incomplete.date_arrive or
                       last_task_incomplete.date_start)
        rebase_x_minutes = (now - last_update) > timedelta(minutes=x_minutes)
        return rebase_x_minutes

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
    FILE_TYPES = [
        ('sheet', 'Hoja'),
        ('split', 'Dividida'),
        ('clone', 'Clonado'),
    ]
    data_file = models.ForeignKey(
        DataFile, related_name="sheet_files", on_delete=models.CASCADE)
    file = models.FileField(
        max_length=255, upload_to=set_upload_sheet_file_path,
        storage=S3Boto3Storage(**params_glacier_ir))
    file_type = models.CharField(max_length=20, blank=True, null=True)

    matched = models.BooleanField(blank=True, null=True)
    sheet_name = models.CharField(max_length=255, blank=True, null=True)
    # En algún momento hay que borrar este campo
    sample_data = JSONField(
        blank=True, null=True, default=default_explore_data)
    sample_file = models.FileField(
        max_length=255, upload_to=set_upload_sheet_file_path,
        blank=True, null=True, verbose_name="Archivo con muestra")
    headers = JSONField(blank=True, null=True)
    row_start_data = models.IntegerField(blank=True, null=True)

    total_rows = models.IntegerField(default=0)
    error_process = JSONField(blank=True, null=True)
    warnings = JSONField(blank=True, null=True)
    # RICK TODO Future: Hay que eliminar este campo
    year_month = models.CharField(
        max_length=8, blank=True, null=True, verbose_name="Año y mes")
    month_records = models.ManyToManyField(
        MonthRecord, blank=True, related_name="sheet_files")
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='explore', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')
    rx_count = models.IntegerField(
        verbose_name="Prescripciones (rx)",
        default=0)
    duplicates_count = models.IntegerField(
        verbose_name="Duplicados",
        default=0)
    shared_count = models.IntegerField(
        verbose_name="Compartidos",
        default=0)
    self_repeated_count = models.IntegerField(
        verbose_name="Repetidos", default=0)
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, default='pending',
        verbose_name="merge behavior")

    def save(self, *args, **kwargs):
        if self.pk and can_delete_s3:
            try:
                old_instance = SheetFile.objects.get(pk=self.pk)
                if old_instance.file and old_instance.file != self.file:
                    old_instance.file.delete(save=False)
            except SheetFile.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        some_inserted = self.laps.filter(inserted=True).exists()
        if some_inserted:
            raise Exception(
                "No se puede eliminar un archivo con datos insertados")
        # if can_delete_s3:
        #     self.file.delete(save=False)
        # else:
        #     print("No se pueden borrar archivos en AWS")
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
        verbose_name = "Archivo de hojas (csv)"
        verbose_name_plural = "4. Archivos de hojas (Sheets .csv)"
        ordering = ["id"]
        unique_together = ("data_file", "sheet_name", "file_type")
        db_table = "inai_sheetfile"


class CrossingSheet(models.Model):
    # provider = models.ForeignKey(
    #     Provider, related_name="crossing_sheets", on_delete=models.CASCADE)
    sheet_file_1 = models.ForeignKey(
        SheetFile, related_name="crossing_1", on_delete=models.CASCADE)
    sheet_file_2 = models.ForeignKey(
        SheetFile, related_name="crossing_2", on_delete=models.CASCADE)
    week_record = models.ForeignKey(
        WeekRecord, related_name="crossing_sheets",
        on_delete=models.CASCADE, blank=True, null=True)
    month_record = models.ForeignKey(
        MonthRecord, related_name="crossing_sheets",
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
    missing_inserted = models.BooleanField(
        default=False, blank=True, null=True)

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
            raise Exception(
                "No se puede eliminar un archivo con datos insertados")
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


params_standard_ia = {"gzip": True, "object_parameters": {
    "StorageClass": "STANDARD_IA"}}


class TableFile(models.Model):

    file = models.FileField(
        max_length=255, upload_to=set_upload_table_file_path,
        storage=S3Boto3Storage(**params_standard_ia))
    lap_sheet = models.ForeignKey(
        LapSheet, related_name="table_files", on_delete=models.CASCADE,
        blank=True, null=True)
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, blank=True, null=True,
        related_name="table_files")
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, blank=True, null=True)
    inserted = models.BooleanField(default=False)
    week_record = models.ForeignKey(
        WeekRecord, on_delete=models.CASCADE,
        blank=True, null=True, related_name="table_files")

    drugs_count = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    self_repeated_count = models.IntegerField(default=0)

    #  ##### Todos estos campos deberían eliminarse, ya están en week_record
    year_week = models.CharField(max_length=8, blank=True, null=True)
    iso_year = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_week = models.PositiveSmallIntegerField(blank=True, null=True)
    iso_delegation = models.ForeignKey(
        Delegation, on_delete=models.CASCADE, blank=True, null=True)
    year_month = models.CharField(max_length=8, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    #  ##### Fin de campos a eliminar ############

    def __str__(self):
        return "%s %s" % (self.collection, self.lap_sheet)

    def save(self, *args, **kwargs):
        if self.pk and can_delete_s3:
            try:
                old_instance = TableFile.objects.get(pk=self.pk)

                if old_instance.file and old_instance.file != self.file:
                    old_instance.file.delete(save=False)
            except TableFile.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if can_delete_s3:
            self.file.delete(save=False)
        else:
            print("No se pueden borrar archivos en AWS")
        super().delete(*args, **kwargs)

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
            "lap_sheet", "collection", "year",
            "iso_week", "iso_delegation")
        db_table = "inai_tablefile"


def final_month_path(month_record, filename):
    elems = get_elems_by_provider(month_record.provider, "month_tables")
    elems.append(month_record.year or "ND")
    return join_path(elems, filename)


def set_upload_month_path(instance, filename):
    return final_month_path(instance.month_record, filename)


def get_month_file_name(
        month_table=None, table_name=None, month_record=None):
    if not table_name:
        table_name = month_table.collection.model_name.lower()
    if not month_record:
        month_record = month_table.month_record
    return f"{month_record.temp_table}_{table_name}.csv"


params_glacier_deep = {"object_parameters": {"StorageClass": "DEEP_ARCHIVE"}}


class MonthTableFile(models.Model):
    month_record = models.ForeignKey(
        MonthRecord, related_name="month_table_files", on_delete=models.CASCADE)
    table_name = models.CharField(max_length=120)
    file = models.FileField(
        max_length=255, upload_to=set_upload_month_path,
        blank=True, null=True, storage=S3Boto3Storage(**params_glacier_deep))
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    inserted = models.BooleanField(default=False)
    available_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.month_record} - {self.collection}"

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    class Meta:
        verbose_name = "Archivo de mes"
        verbose_name_plural = "7. Archivos de mes"
