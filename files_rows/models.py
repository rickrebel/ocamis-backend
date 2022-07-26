from django.db import models
from django.contrib.postgres.fields import JSONField

from catalog.models import Entity
from files_categories.models import (
    StatusControl, TypeFile, ColumnType, NegativeReason)
from parameter.models import TypeData, FinalField, CleanFunction


"""class ControlParameters(models.Model):
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE)
    start_month = models.CharField(max_length=80)
    end_month = models.CharField(max_length=80)
    notes = models.TextField(blank=True, null=True)
    many_months = models.BooleanField(default=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Parametro de control"
        verbose_name_plural = u"Parametros de control" """

class Petition(models.Model):
    entity = models.ForeignKey(
        Entity,
        related_name="petitions",
        on_delete=models.CASCADE)
    date_send = models.DateTimeField(blank=True, null=True)
    limit_response = models.DateTimeField(blank=True, null=True)
    date_response = models.DateTimeField(blank=True, null=True)
    limit_pickup = models.DateTimeField(
        blank=True, null=True, verbose_name="límite para recoger datos")
    limit_complain = models.DateTimeField(
        blank=True, null=True,
        verbose_name="límite para presentar queja")
    ask_extension = models.NullBooleanField(
        blank=True, null=True,
        verbose_name="Se solicitó extensión")
    notes = models.TextField(blank=True, null=True)
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
    negative_reason = models.ForeignKey(
        NegativeReason, null=True, blank=True, 
        verbose_name="Razón de la negativa",
        on_delete=models.CASCADE)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.id)

    class Meta:
        verbose_name = u"Solicitud"
        verbose_name_plural = u"Solicitudes"


class GroupFile(models.Model):

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

    #control_parameters= models.ForeignKey(
    #    ControlParameters, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=120, default='grupo único')
    type_file = models.ForeignKey(
        TypeFile, on_delete=models.CASCADE)
    format_file = models.CharField(
        max_length=5,
        choices=FORMAT_CHOICES,
        null=True,
        blank=True)
    other_format = models.CharField(max_length=80, blank=True, null=True)
    final_data = models.NullBooleanField(
        verbose_name="Es información final")
    notes = models.TextField(blank=True, null=True)
    row_start_data = models.IntegerField(
        default=1, verbose_name='# de fila donde inician los datos')
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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo de archivos"
        verbose_name_plural = u"Grupos de archivos"


class PetitionGroupFile(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="file_groups",
        on_delete=models.CASCADE)
    group_file = models.ForeignKey(
        GroupFile, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.petition, self.group_file)

    class Meta:
        verbose_name = u"Relacional: petición -- group_file"
        verbose_name_plural = u"Relacional: petición -- group_file"


class MonthEntity(models.Model):
    entity = models.ForeignKey(
        Entity, 
        related_name="months",
        on_delete=models.CASCADE)
    year_month = models.CharField(max_length=10)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.year_month)

    class Meta:
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
        return "%s, %s" % (self.petition, self.monthentity)

    class Meta:
        verbose_name = u"Mes de peticion"
        verbose_name_plural = u"Meses de peticion"


class DataFile(models.Model):
    #group_file = models.ForeignKey(
    #    GroupFile, on_delete=models.CASCADE)
    #petition = models.ForeignKey(
    #    Petition, on_delete=models.CASCADE)
    ori_file = models.FileField(max_length=100) 
    date = models.DateTimeField(auto_now_add=True)
    month_entity = models.ForeignKey(
        MonthEntity, blank=True, null=True,
        on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    #is_final = models.BooleanField(default= True)
    origin_file = models.ForeignKey(
        "DataFile",
        blank=True, null=True, related_name="child_files",
        on_delete=models.CASCADE)
    petition_group_file = models.ForeignKey(
        PetitionGroupFile,
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

    def __str__(self):
        return self.ori_file

    def save_errors(self, errors, error_name):
        errors = ['No se pudo descomprimir el archivo gz']
        curr_errors = self.errors_process or []
        curr_errors += errors
        current_status, created = StatusControl.objects.get_or_create(
            name=error_name)
        self.error_process = curr_errors
        self.status_process = current_status 
        print(curr_errors)
        self.save()

    class Meta:
        verbose_name = u"Archivo con datos"
        verbose_name_plural = u"Archivos con datos"


class ProcessFile(models.Model):
    petition = models.ForeignKey(
        Petition,
        related_name="process_files",
        on_delete=models.CASCADE)
    ori_file = models.FileField(max_length=100) 
    date = models.DateTimeField(auto_now_add=True)
    type_file = models.ForeignKey(
        TypeFile, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.ori_file, self.petition)

    class Meta:
        verbose_name = u"Documento"
        verbose_name_plural = u"Documentos"


class NameColumn (models.Model):
    name_in_data = models.TextField(blank=True, null=True)
    position_in_data = models.IntegerField(default=1)
    column_type=models.ForeignKey(
        ColumnType, on_delete=models.CASCADE)
    #parameter = models.ForeignKey(
    #    Parameter, 
    #    blank=True, null=True,
    #    on_delete=models.CASCADE)
    group_file = models.ForeignKey(
        GroupFile,
        related_name="columns",
        blank=True, null=True,
        on_delete=models.CASCADE)
    type_data = models.ForeignKey(
        TypeData, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    final_field = models.ForeignKey(
        FinalField, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    clean_params = JSONField(
        blank=True, null=True) 
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
        verbose_name="Función de limpieza o tranformación")
    group_file = models.ForeignKey(
        GroupFile, 
        related_name="group_tranformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Grupo de archivos")
    column = models.ForeignKey(
        NameColumn, 
        related_name="column_tranformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Columna")
    addl_params = JSONField(blank=True, null=True)
