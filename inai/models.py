from django.db import models
from django.db.models import JSONField

from geo.models import Agency
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


def set_upload_path(instance, filename):
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
        last_year_month = instance.month_agency.year_month
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


class Petition(models.Model, PetitionTransformsMix):

    folio_petition = models.CharField(
        max_length=50,
        verbose_name="Folio de la solicitud")
    agency = models.ForeignKey(
        Agency,
        related_name="petitions",
        on_delete=models.CASCADE)
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

    def delete(self, *args, **kwargs):
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__petition=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

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


class MonthAgency(models.Model):
    agency = models.ForeignKey(
        Agency,
        related_name="months",
        on_delete=models.CASCADE)
    year_month = models.CharField(max_length=10)

    def __str__(self):
        return "%s -- %s" % (self.agency, self.year_month)

    @property
    def human_name(self):
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        month_numb = int(self.year_month[-2:])
        month_name = months[month_numb-1]
        return "%s/%s" % (month_name, self.year_month[:-2])

    class Meta:
        get_latest_by = "year_month"
        verbose_name = "Mes de entidad"
        verbose_name_plural = "Meses de entidad"


class PetitionMonth(models.Model):
    petition = models.ForeignKey(
        Petition, 
        related_name="petition_months",
        on_delete=models.CASCADE)
    month_agency = models.ForeignKey(
        MonthAgency, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s-> %s, %s" % (self.id, self.petition, self.month_agency)

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
        FileType, on_delete=models.CASCADE, blank=True, null=True)
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
    zip_path = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    petition_month = models.ForeignKey(
        PetitionMonth, blank=True, null=True,
        on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    # is_final = models.BooleanField(default= True)
    origin_file = models.ForeignKey(
        "DataFile", blank=True, null=True, related_name="child_files",
        verbose_name="archivo origen", on_delete=models.CASCADE)
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

    file_type = models.ForeignKey(
        FileType, blank=True, null=True, on_delete=models.CASCADE,
        default='original_data',
        verbose_name="Tipo de archivo")

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
    completed_rows = models.IntegerField(default=0)
    inserted_rows = models.IntegerField(default=0)

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
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='explore', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')
    # completed_rows = models.IntegerField(default=0)
    # inserted_rows = models.IntegerField(default=0)
    # all_results = JSONField(blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        some_inserted = self.laps.filter(inserted=True).exists()
        if some_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(using, keep_parents)

    # def save(self, *args, **kwargs):
    #     if self.pk:
    #         some_inserted = self.laps.filter(inserted=True).exists()
    #         if some_inserted:
    #             raise Exception("No se puede modificar un archivo con datos insertados")
    #     super().save(*args, **kwargs)

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

    def check_success_insert(self, task_params=None, **kwargs):
        from task.models import AsyncTask
        # from inai.data_file_mixins.insert_mix import modify_constraints
        # import threading
        # import time

        # def check_tasks_with_insert():
        #     running_tasks = AsyncTask.objects.filter(
        #         data_file__stage_id="insert",
        #         data_file__status__is_completed=False)
        #     if not running_tasks.exists():
        #         modify_constraints(is_create=True)
        #
        # def delay_check():
        #     time.sleep(20)
        #     check_tasks_with_insert()
        #
        # t = threading.Thread(target=delay_check)
        # t.start()
        errors = kwargs.get("errors", [])
        self.save_stage('insert', errors)
        return [], errors, True

    def build_csv_data_from_aws(self, task_params=None, **kwargs):
        from django.utils import timezone
        # print("FINISH BUILD CSV DATA")
        data_file = self.data_file
        is_prepare = kwargs.get("is_prepare", False)
        # sheet_file_id = kwargs.get("sheet_file_id", None)
        # sheet_file = SheetFile.objects.get(id=sheet_file_id)
        # print("is_prepare", is_prepare)
        next_lap = self.next_lap if not is_prepare else -1
        # print("next_lap", next_lap)
        # print("next_lap", sheet_file.next_lap)
        # print("final_paths", final_paths)
        report_errors = kwargs.get("report_errors", {})
        lap_sheet, created = LapSheet.objects.get_or_create(
            sheet_file=self, lap=next_lap)
        fields_in_report = report_errors.keys()
        for field in fields_in_report:
            setattr(lap_sheet, field, report_errors[field])
        lap_sheet.last_edit = timezone.now()
        lap_sheet.save()

        if not is_prepare and not \
                data_file.petition_file_control.file_control.decode:
            decode = kwargs.get("decode", None)
            if decode:
                data_file.petition_file_control.file_control.decode = decode
                data_file.petition_file_control.file_control.save()

        error_fields = ["missing_rows", "missing_fields"]
        errors_count = sum([report_errors[field] for field in error_fields])
        total_rows = report_errors["total_count"] - report_errors["discarded_count"]
        errors = []
        if not total_rows:
            errors.append("No se encontraron filas")
        elif errors_count / total_rows > 0.05:
            errors.append("Se encontraron demasiados errores en filas/campos")
        stage_id = "prepare" if is_prepare else "transform"

        if is_prepare or errors:
            self.save_stage(stage_id, errors)
            return [], errors, True
        # data_file.all_results = kwargs.get("report_errors", {})
        # data_file.save()
        final_paths = kwargs.get("final_paths", []) or []
        new_task, errors, data = lap_sheet.save_result_csv(final_paths)
        self.save_stage(stage_id, errors)
        return new_task, errors, data

    def __str__(self):
        return f">{self.file_type}< {self.sheet_name}- {self.data_file}"

    class Meta:
        verbose_name = "Archivo csv"
        verbose_name_plural = "4. Archivos csv"
        ordering = ["id"]
        unique_together = ("data_file", "sheet_name", "file_type")


class LapSheet(models.Model):

    sheet_file = models.ForeignKey(
        SheetFile, related_name="laps", on_delete=models.CASCADE)
    lap = models.IntegerField(default=0)
    last_edit = models.DateTimeField(blank=True, null=True)
    inserted = models.BooleanField(default=False, blank=True, null=True)

    general_error = models.CharField(max_length=255, blank=True, null=True)
    total_count = models.IntegerField(default=0)
    processed_count = models.IntegerField(default=0)
    prescription_count = models.IntegerField(default=0)
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

    def save_result_csv(self, result_files):
        all_new_files = []
        new_tasks = []
        new_file_ids = []
        for result_file in result_files:
            model_name = result_file["model"]
            print("model_name", model_name)
            collection = Collection.objects.get(model_name=model_name)
            new_file, created = TableFile.objects.get_or_create(
                lap_sheet=self,
                collection=collection,
            )
            new_file_ids.append(new_file.id)
            new_file.file = result_file["path"]
            new_file.save()
            # new_file.change_status('initial|finished')
            all_new_files.append(new_file)
            # new_tasks = self.send_csv_to_db(result_file["path"], model_name)
            # new_tasks.append(new_tasks)
        TableFile.objects.filter(lap_sheet=self)\
                         .exclude(id__in=new_file_ids)\
                         .delete()
        return new_tasks, [], all_new_files

    # def confirm_all_inserted(self):
    #     pending_tables = self.table_files.filter(inserted=False).exists()
    #     self.inserted = None if pending_tables else True
    #     self.save()
    #     return not pending_tables

    def __str__(self):
        return "%s %s" % (str(self.sheet_file), self.lap)

    class Meta:
        verbose_name = "Lap de archivo csv"
        verbose_name_plural = "5. Laps de archivo csv"
        ordering = ["id"]
        unique_together = ("sheet_file", "lap")


class TableFile(models.Model):

    # sheet_file = models.ForeignKey(
    #     SheetFile, related_name="process_files", on_delete=models.CASCADE)
    lap_sheet = models.ForeignKey(
        LapSheet, related_name="table_files", on_delete=models.CASCADE)
    file = models.FileField(max_length=255, upload_to=set_upload_path)
    # file_type = models.ForeignKey(
    #     FileType, on_delete=models.CASCADE, blank=True, null=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, blank=True, null=True)
    is_for_edition = models.BooleanField(default=False)
    # inserted = models.BooleanField(default=False)

    def __str__(self):
        return "%s %s" % (self.collection, self.lap_sheet)

    class Meta:
        verbose_name = "Archivo para insertar"
        verbose_name_plural = "6. Archivos para insertar"
        ordering = ["id"]
        unique_together = ("lap_sheet", "collection", "is_for_edition")
