import os

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.deconstruct import deconstructible

from catalog.models import Entity
from category.models import (
    StatusControl, FileType, ColumnType, NegativeReason, DateBreak, Anomaly)
from data_param.models import (
    DataType, FinalField, CleanFunction, DataGroup, Collection)

from .data_file_mixins.explore_mix import ExploreMix
from .data_file_mixins.utils_mix import DataUtilsMix
from .data_file_mixins.matches_mix import MatchesMix
from .data_file_mixins.get_data_mix import ExtractorsMix


def set_upload_path(instance, filename):
    #from django.conf import settings
    #files_path = getattr(settings, "FILES_PATH")
    try:
        petition = instance.petition_file_control.petition
    except:
        try:
            petition = instance.petition
        except Exception as e:
            return "/".join(["sin_instance" ,filename])

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


class Petition(models.Model):
    folio_petition = models.CharField(
        max_length=50,
        verbose_name="Folio de la solicitud")
    entity = models.ForeignKey(
        Entity,
        related_name="petitions",
        on_delete=models.CASCADE)
    ask_extension = models.NullBooleanField(
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

    def first_year_month(self):
        return self.petition_months.earliest().month_entity.year_month

    def last_year_month(self):
        return self.petition_months.latest().month_entity.year_month

    def months(self):
        html_list = ''
        start = self.petition_months.earliest().month_entity.human_name
        end = self.petition_months.latest().month_entity.human_name
        return " ".join(list(set([start, end])))
    months.short_description = u"Meses"

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
    months_in_description.short_description = u"Meses escritos"


    def __str__(self):
        return "%s -- %s" % (self.entity, self.id)

    class Meta:
        verbose_name = u"Solicitud - Petición"
        verbose_name_plural = u"Solicitudes (Petiticiones)"


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
    def default_addl_params():
        return {"need_partition": True, "need_transform": False}

    name = models.CharField(
        max_length=255, default='grupo único')
    file_type = models.ForeignKey(
        FileType, on_delete=models.CASCADE,
        blank=True, null=True,)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE)
    format_file = models.CharField(
        max_length=5,
        choices=FORMAT_CHOICES,
        null=True, blank=True)
    other_format = models.CharField(max_length=80, blank=True, null=True)
    final_data = models.NullBooleanField(
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
        return self.name

    class Meta:
        unique_together = ["data_group", "name"]
        verbose_name = "Grupo control de archivos"
        verbose_name_plural = "Grupos control de archivos"


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
        verbose_name = u"Relacional: petición -- file_control"
        verbose_name_plural = u"Relacional: petición -- file_control"


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


class DataFile(models.Model, ExploreMix, DataUtilsMix, ExtractorsMix):

    file = models.FileField(max_length=150, upload_to=set_upload_path) 
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
        on_delete=models.CASCADE)
    petition_file_control = models.ForeignKey(
        PetitionFileControl,
        related_name="data_files",
        blank=True, null=True,
        on_delete=models.CASCADE)
    status_process = models.ForeignKey(
        StatusControl,
        blank=True, null=True,
        on_delete=models.CASCADE)
    error_process = JSONField(blank=True, null=True)
    inserted_rows = models.IntegerField(default=1)
    completed_rows = models.IntegerField(default=1)
    total_rows = models.IntegerField(default=1)

    @property
    def final_path(self):
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        return self.file.url if is_prod else self.file.path

        return self.petition_months.earliest().month_entity.year_month

    def __str__(self):
        return "%s %s" % (str(self.file), self.petition_file_control)
        #return "%s %s" % (self.petition_file_control, self.date)
        #return "hola"

    class Meta:
        ordering = ["file"]
        verbose_name = u"Archivo con datos"
        verbose_name_plural = u"Archivos con datos"


class ProcessFile(models.Model):

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

    def __str__(self):
        first = (self.file or (self.text and self.text[:80]) 
            or self.url_download or 'None')
        return "%s -- %s" % (first, self.petition)

    class Meta:
        verbose_name = u"Documento"
        verbose_name_plural = u"Documentos"


class NameColumn (models.Model):
    name_in_data = models.TextField(
        verbose_name="Nombre de la columna real", blank=True, null=True)
    position_in_data = models.IntegerField(
        default=1, blank=True, null=True)
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
    clean_params = JSONField(blank=True, null=True,
        verbose_name="Parámetros de limpieza")
    requiered_row = models.BooleanField(default=False)
    parent_row = models.ForeignKey(
        "NameColumn", related_name="parents",
        verbose_name="Columna padre de la que derivó", 
        blank=True, null=True, on_delete=models.CASCADE)
    children_row = models.ForeignKey(
        "NameColumn", related_name="childrens",
        verbose_name="Hijo resultado (junto a otras columnas)",
        blank=True, null=True, on_delete=models.CASCADE)


    def __str__(self):
        return "%s -- %s" % (self.name_in_data, self.position_in_data)

    class Meta:
        verbose_name = u"Nombre de Columna"
        verbose_name_plural = u"Nombres de Columnas"   


class Transformation(models.Model):
    clean_function = models.ForeignKey(
        CleanFunction, 
        on_delete=models.CASCADE,
        verbose_name="Función de limpieza o transformación")
    file_control = models.ForeignKey(
        FileControl, 
        related_name="file_tranformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Grupo de archivos")
    name_column = models.ForeignKey(
        NameColumn, 
        related_name="column_tranformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Columna")
    addl_params = JSONField(blank=True, null=True)
