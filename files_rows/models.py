from django.db import models
from django.contrib.postgres.fields import JSONField

from catalog.models import Entity
from files_categories.models import FormatFile, StatusProcessing, TypeFile

from recipe.models import RecipeReport2, RecipeMedicine2
from parameter.models import Parameter, TypeData, FinalField


class ControlParameters(models.Model):
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
        verbose_name_plural = u"Parametros de control"


class Petition(models.Model):
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE)
    control_parameters = models.ForeignKey(
        ControlParameters, blank=True, null=True, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    date_send = models.DateTimeField(blank=True, null=True)
    date_response = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.control_parameters)

    class Meta:
        verbose_name = u"Solicitud"
        verbose_name_plural = u"Solicitudes"


class GroupFile(models.Model):
    
    def default_addl_params():
        return {"need_partition": True, "need_transform": False}

    control_parameters= models.ForeignKey(
        ControlParameters, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=120, default='grupo único')
    type_file = models.ForeignKey(
        TypeFile, on_delete=models.CASCADE)
    format_file = models.ForeignKey(
        FormatFile, on_delete=models.CASCADE)
    final_data = models.NullBooleanField(
        verbose_name="Es información final")
    notes = models.TextField(blank=True, null=True)
    in_percent = models.BooleanField(default= False)
    addl_params = JSONField(default=default_addl_params)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo de archivos"
        verbose_name_plural = u"Grupos de archivos"


class MonthEntity(models.Model):
    entity = models.ForeignKey(
        Entity,  on_delete=models.CASCADE)
    year_month = models.CharField(max_length=10)

    def __str__(self):
        return "%s -- %s" % (self.entity, self.year_month)

    class Meta:
        verbose_name = u"Mes de entidad"
        verbose_name_plural = u"Meses de entidad"


class PetitionMonth(models.Model):
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE)
    monthentity = models.ForeignKey(
        MonthEntity, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s, %s" % (self.petition, self.monthentity)

    class Meta:
        verbose_name = u"Mes de peticion"
        verbose_name_plural = u"Meses de peticion"


class File(models.Model):
    group_file = models.ForeignKey(
        GroupFile, on_delete=models.CASCADE)
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE)
    ori_file = models.FileField(max_length=100) 
    date = models.DateTimeField(blank=True, null=True)
    petition_month = models.ForeignKey(
        PetitionMonth, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    is_final = models.BooleanField(default= True)
    origen_file = models.ForeignKey("self", on_delete=models.CASCADE)
    status_processing = models.ForeignKey(
        StatusProcessing,
        blank=True, null=True,
        on_delete=models.CASCADE)
    inserted_rows = models.IntegerField(default=1)
    completed_rows = models.IntegerField(default=1)
    total_rows = models.IntegerField(default=1)

    def __str__(self):
        return "%s -- %s" % (self.group_file, self.petition)

    def save_errors(self, errors, error_name):
        from files_categories.models import StatusProcess
        errors = ['No se pudo descomprimir el archivo gz']
        curr_errors = self.errors_process or []
        curr_errors += errors
        current_status, created = StatusProcess.objects.get_or_create(
            name=error_name)
        self.error_process = curr_errors
        self.status_process = current_status 
        print(curr_errors)
        self.save()

    class Meta:
        verbose_name = u"Documento"
        verbose_name_plural = u"Documentos"


class MissingRows(models.Model):
    file = models.ForeignKey(
        File, on_delete=models.CASCADE)
    recipe_report = models.ForeignKey(
        RecipeReport2, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    recipe_medicine = models.ForeignKey(
        RecipeMedicine2, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    original_data = JSONField(
        blank=True, null=True)
    row_seq = models.IntegerField(default=1)
    tab = models.CharField(max_length=255)

    def __str__(self):
        return "%s -- %s" % (self.file, self.recipe_report or self.recipe_medicine)

    class Meta:
        verbose_name = u"Renglón faltante"
        verbose_name_plural = u"Renglones faltantes"   


class Column (models.Model):
    name_in_data = models.TextField(blank=True, null=True)
    position_in_data = models.IntegerField(default=1)
    parameter = models.ForeignKey(
        Parameter, 
        blank=True, null=True,
        on_delete=models.CASCADE)
    group_file = models.ForeignKey(
        GroupFile, 
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
    requiered_row= models.BooleanField(default= False)

    def __str__(self):
        return "%s -- %s" % (self.name_in_data, self.position_in_data)

    class Meta:
        verbose_name = u"Columna"
        verbose_name_plural = u"Columnas"   


class MissingFields(models.Model):
    missing_row = models.ForeignKey(
        MissingRows,
        on_delete=models.CASCADE)
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE)
    original_value = models.TextField(blank=True, null=True)
    final_value = models.TextField(blank=True, null=True)
    other_values = JSONField(
        blank=True, null=True)
    errors = JSONField(
        blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.missing_row, self.column)

    class Meta:
        verbose_name = u"Documento Faltante"
        verbose_name_plural = u"Documentos Faltantes"   
