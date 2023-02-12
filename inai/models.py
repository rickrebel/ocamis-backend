import os

from django.db import models
from django.db.models import JSONField

from django.contrib.auth.models import User
from catalog.models import Entity
from category.models import (
    StatusControl, FileType, ColumnType, NegativeReason, 
    DateBreak, Anomaly, InvalidReason, FileFormat, StatusTask)
from data_param.models import (
    DataType, FinalField, CleanFunction, DataGroup, Collection, ParameterGroup)

from .data_file_mixins.explore_mix import ExploreMix
from .data_file_mixins.utils_mix import DataUtilsMix
from .data_file_mixins.get_data_mix import ExtractorsMix
from .process_file_mixins.process_mix import ProcessFileMix
from .petition_mixins.petition_mix import PetitionMix, PetitionTransformsMix


def set_upload_path(instance, filename):
    #from django.conf import settings
    #files_path = getattr(settings, "FILES_PATH")
    try:
        petition = instance.petition_file_control.petition
    except:
        try:
            petition = instance.petition
        except Exception as e:
            return "/".join(["sin_instance", filename])

    entity_type = petition.entity.entity_type[:8].lower()
    try:
        acronym = petition.entity.acronym.lower()

    except:
        acronym = 'others'
    try:
        last_year_month = instance.month_entity.year_month
    except AttributeError:
        try:
            #last_year_month = petition.petition_months[-1].month_entity.year_month
            last_year_month = petition.last_year_month()
        except :
            last_year_month = "others"
    except:
        last_year_month = "others"
    #final_path = "/".join([entity_type, acronym, last_year_month, filename])
    #print(os.path.join('/media/%s/' % instance.id, filename))
    #print(os.path.join(files_path, final_path))
    return "/".join([entity_type, acronym, last_year_month, filename])


class Petition(models.Model, PetitionTransformsMix):

    folio_petition = models.CharField(
        max_length=50,
        verbose_name="Folio de la solicitud")
    entity = models.ForeignKey(
        Entity,
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
        help_text="Información de la queja en INAI Seach",
        blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.folio_petition or self.id)

    class Meta:
        verbose_name = u"Solicitud - Petición"
        verbose_name_plural = u"Solicitudes (Peticiones)"


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


def default_addl_params():
    return {"need_partition": True, "need_transform": False}


class FileControl(models.Model):

    FORMAT_CHOICES = (
        ("pdf", "PDF"),
        ("word", "Word"),
        ("xls", "Excel"),
        ("txt", "Texto"),
        ("csv", "CSV"),
        ("email", "Correo electrónico"),
        ("other", "Otro"),
    )

    name = models.CharField(max_length=255)
    file_type = models.ForeignKey(
        FileType, on_delete=models.CASCADE,
        blank=True, null=True,)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE)
    format_file = models.CharField(
        max_length=5,
        choices=FORMAT_CHOICES,
        null=True, blank=True)
    file_format = models.ForeignKey(
        FileFormat, verbose_name="formato del archivo",
        blank=True, null=True, on_delete=models.CASCADE)
    other_format = models.CharField(max_length=80, blank=True, null=True)
    final_data = models.BooleanField(
        verbose_name="Es información final", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    row_start_data = models.IntegerField(
        default=1, verbose_name='# de fila donde inician los datos',
        blank=True, null=True)
    row_headers = models.IntegerField(
        blank=True, null=True,
        verbose_name='# de fila donde se encuentran los encabezados')
    in_percent = models.BooleanField(default= False)
    addl_params = JSONField(default=default_addl_params)
    delimiter = models.CharField(
        max_length=3, blank=True, null=True, 
        verbose_name="Delimitador de columnas")
    status_register = models.ForeignKey(
        StatusControl, null=True, blank=True, 
        verbose_name="Status de los registro de variables",
        on_delete=models.CASCADE)
    anomalies = models.ManyToManyField(
        Anomaly, verbose_name="Anomalías de los datos", blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        #all_entities = Entity.objects.filter(
        #    petitions__file_controls__petition__entity=self).distinct()\
        #        .value_list("acronym", flat=True)
        return f"{self.id}. {self.name}"
        #return self.name

    class Meta:
        #unique_together = ["data_group", "name"]
        verbose_name = "Grupo de control de archivos"
        verbose_name_plural = "Grupos de control de archivos"


class PetitionFileControl(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="file_controls",
        on_delete=models.CASCADE)
    file_control = models.ForeignKey(
        FileControl, on_delete=models.CASCADE,
        related_name="petition_file_control",)

    def __str__(self):
        return "%s - %s" % (self.petition, self.file_control)

    class Meta:
        verbose_name = u"Relacional: petición -- Grupo de Control"
        verbose_name_plural = u"Relacional: Petición -- Grupos de Control"


class MonthEntity(models.Model):
    entity = models.ForeignKey(
        Entity, 
        related_name="months",
        on_delete=models.CASCADE)
    year_month = models.CharField(max_length=10)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.year_month)

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
        verbose_name = u"Mes de entidad"
        verbose_name_plural = u"Meses de entidad"


class PetitionMonth(models.Model):
    petition = models.ForeignKey(
        Petition, 
        related_name="petition_months",
        on_delete=models.CASCADE)
    month_entity = models.ForeignKey(
        MonthEntity, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s-> %s, %s" % (self.id, self.petition, self.month_entity)

    class Meta:
        get_latest_by = "month_entity__year_month"
        verbose_name = u"Mes de peticion"
        verbose_name_plural = u"Meses de peticion"


def default_explore_data():
    return {}


class DataFile(models.Model, ExploreMix, DataUtilsMix, ExtractorsMix):

    file = models.FileField(max_length=150, upload_to=set_upload_path)
    zip_path = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    petition_month = models.ForeignKey(
        PetitionMonth, blank=True, null=True,
        on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    #is_final = models.BooleanField(default= True)
    origin_file = models.ForeignKey(
        "DataFile",
        blank=True, null=True,
        related_name="child_files",
        verbose_name="archivo origen",
        on_delete=models.CASCADE)
    process_file = models.ForeignKey(
        "ProcessFile", blank=True, null=True, 
        on_delete=models.CASCADE, verbose_name="archivo base",
        related_name="data_file_childs")
    petition_file_control = models.ForeignKey(
        PetitionFileControl,
        related_name="data_files",
        blank=True, null=True,
        on_delete=models.CASCADE)
    status_process = models.ForeignKey(
        StatusControl,
        blank=True, null=True,
        on_delete=models.CASCADE)
    #jump_columns = models.IntegerField(
    #    default=0, verbose_name="Columnas vacías al comienzo")
    explore_data = JSONField(
        blank=True, null=True,
        verbose_name="Primeros datos, de exploración")
    sheet_names = JSONField(
        blank=True, null=True,
        verbose_name="Nombres de las hojas")
    directory = models.CharField(
        max_length=255, verbose_name="Ruta en archivo comprimido",
        blank=True, null=True)
    error_process = JSONField(
        blank=True, null=True, verbose_name="Errores de procesamiento")
    all_results = JSONField(
        blank=True, null=True, verbose_name="Todos los resultados")
    inserted_rows = models.IntegerField(default=1)
    completed_rows = models.IntegerField(default=1)
    total_rows = models.IntegerField(default=1)

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

    """def save(self, *args, **kwargs):
        print("saving datafile: ")
        print(bool(self.explore_data))
        print(self.explore_data)
        super(DataFile, self).save(*args, **kwargs)"""

    def __str__(self):
        return "%s %s" % (str(self.file), self.petition_file_control)
        #return "%s %s" % (self.petition_file_control, self.date)
        #return "hola"

    class Meta:
        ordering = ["file"]
        verbose_name = u"Archivo con datos"
        verbose_name_plural = u"Archivos con datos"


class ProcessFile(models.Model, ProcessFileMix):

    petition = models.ForeignKey(
        Petition,
        related_name="process_files",
        on_delete=models.CASCADE)
    file = models.FileField(
        verbose_name="arhivo",
        max_length=150, upload_to=set_upload_path,
        blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    file_type = models.ForeignKey(
        FileType, on_delete=models.CASCADE, blank=True, null=True)
    text = models.TextField(blank=True, null=True, 
        verbose_name="Texto (en caso de no haber archivo)")
    url_download = models.URLField(
        max_length=400, blank=True, null=True, 
        verbose_name="Url donde se puede descargar el archivo")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")
    addl_params = JSONField(
        blank=True, null=True, verbose_name="Otras configuraciones")
    has_data = models.BooleanField(
        default=False, verbose_name="Contiene los datos")

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
        verbose_name = u"Archivo sin datos finales"
        verbose_name_plural = u"Archivos sin datos finales"


class NameColumn (models.Model):
    name_in_data = models.TextField(
        verbose_name="Nombre de la columna real", blank=True, null=True)
    position_in_data = models.IntegerField(
        blank=True, null=True, verbose_name="idx")
    column_type = models.ForeignKey(
        ColumnType, on_delete=models.CASCADE)
    file_control = models.ForeignKey(
        FileControl,
        related_name="columns",
        blank=True, null=True,
        on_delete=models.CASCADE)
    data_type = models.ForeignKey(
        DataType, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    collection = models.ForeignKey(
        Collection, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    final_field = models.ForeignKey(
        FinalField, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    #parameter_group = models.ForeignKey(
    #    ParameterGroup, 
    #    blank=True, null=True,
    #    on_delete=models.CASCADE)
    clean_params = JSONField(blank=True, null=True,
        verbose_name="Parámetros de limpieza")
    requiered_row = models.BooleanField(default=False)
    parent_column = models.ForeignKey(
        "NameColumn", related_name="parents",
        verbose_name="Columna padre de la que derivó", 
        blank=True, null=True, on_delete=models.CASCADE)
    children_column = models.ForeignKey(
        "NameColumn", related_name="childrens",
        verbose_name="Hijo resultado (junto a otras columnas)",
        blank=True, null=True, on_delete=models.CASCADE)
    seq = models.IntegerField(
        blank=True, null=True, verbose_name="order",
        help_text="Número consecutivo para ordenación en dashboard")

    def __str__(self):
        return "%s-%s | %s" % (
            self.name_in_data, self.position_in_data, self.final_field or '?')

    class Meta:
        ordering = ["seq"]
        verbose_name = "Nombre de Columna"
        verbose_name_plural = "Nombres de Columnas"   


def default_params():
    return {}


class Transformation(models.Model):

    clean_function = models.ForeignKey(
        CleanFunction, 
        on_delete=models.CASCADE,
        verbose_name="Función de limpieza o transformación")
    file_control = models.ForeignKey(
        FileControl, 
        related_name="file_transformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Grupo de archivos")
    name_column = models.ForeignKey(
        NameColumn, 
        related_name="column_transformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Columna")
    addl_params = JSONField(
        blank=True, null=True, default=default_params)

    class Meta:
        verbose_name = "Transformación a aplicar"
        verbose_name_plural = "Transformaciones a aplicar"   


class AsyncTask(models.Model):

    request_id = models.CharField(max_length=100, blank=True, null=True)
    parent_task = models.ForeignKey(
        "self", related_name="child_tasks",
        blank=True, null=True, on_delete=models.CASCADE)
    file_control = models.ForeignKey(
        FileControl,
        related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    petition = models.ForeignKey(
        Petition,
        blank=True, null=True,
        related_name="async_tasks",
        on_delete=models.CASCADE)
    data_file = models.ForeignKey(
        DataFile,
        related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    process_file = models.ForeignKey(
        ProcessFile,
        related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    # status = models.CharField(
    #     max_length=100, blank=True, null=True,
    #     verbose_name="Estado de la tarea")
    status_task = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Estado de la tarea")
    function_name = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Nombre de la función")
    function_after = models.CharField(
        max_length=100, blank=True, null=True)
    original_request = JSONField(
        blank=True, null=True, verbose_name="Request original")
    params_after = JSONField(
        blank=True, null=True, verbose_name="Parámetros de la función after")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    result = JSONField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.function_name, self.status_task)

    class Meta:
        ordering = ["-date_start"]
        verbose_name = "Tarea asincrónica"
        verbose_name_plural = "Tareas asincrónicas"
