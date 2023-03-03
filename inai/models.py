from django.db import models
from django.db.models import JSONField

from catalog.models import Entity
from category.models import (
    StatusControl, FileType, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat)
from transparency.models import Anomaly
from data_param.models import (
    DataType, FinalField, CleanFunction, DataGroup, Collection, ParameterGroup, FileControl)

from .data_file_mixins.explore_mix import ExploreMix
from .data_file_mixins.utils_mix import DataUtilsMix
from .data_file_mixins.get_data_mix import ExtractorsMix
# from .data_file_mixins.matches_mix import MatchesMix
from .process_file_mixins.process_mix import ReplyFileMix

from .petition_mixins.petition_mix import PetitionTransformsMix


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
        verbose_name = "Solicitud - Petición"
        verbose_name_plural = "Solicitudes (Peticiones)"


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

    def __str__(self):
        return "%s - %s" % (self.petition, self.file_control)

    class Meta:
        verbose_name = "Relacional: petición -- Grupo de Control"
        verbose_name_plural = "Relacional: Petición -- Grupos de Control"


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
        verbose_name = "Mes de entidad"
        verbose_name_plural = "Meses de entidad"


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
        verbose_name = "Mes de peticion"
        verbose_name_plural = "Meses de peticion"


def default_explore_data():
    return {}


class ReplyFile(models.Model, ReplyFileMix):

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
        verbose_name_plural = "Archivos sin datos finales"


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
    process_file = models.ForeignKey(
        ReplyFile, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="archivo base", related_name="data_file_childs")
    petition_file_control = models.ForeignKey(
        PetitionFileControl, related_name="data_files", blank=True, null=True,
        on_delete=models.CASCADE)
    status_process = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE)
    file_type = models.ForeignKey(
        FileType, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="Tipo de archivo")
    #jump_columns = models.IntegerField(
    #    default=0, verbose_name="Columnas vacías al comienzo")
    sample_data = JSONField(
        blank=True, null=True, verbose_name="Primeros datos, de exploración")
    sheet_names = JSONField(
        blank=True, null=True, verbose_name="Nombres de las hojas")
    suffix = models.CharField(
        max_length=10, blank=True, null=True)
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
        print(bool(self.sample_data))
        print(self.sample_data)
        super(DataFile, self).save(*args, **kwargs)"""

    def __str__(self):
        return "%s %s" % (str(self.file), self.petition_file_control)
        #return "%s %s" % (self.petition_file_control, self.date)
        #return "hola"

    class Meta:
        ordering = ["file"]
        verbose_name = "Archivo con datos"
        verbose_name_plural = "Archivos con datos"

