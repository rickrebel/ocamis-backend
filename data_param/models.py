#Para qué era esta importación?
# from unicodedata import name
from django.db import models
from django.db.models import JSONField

from category.models import ColumnType, FileFormat, StatusControl
from transparency.models import Anomaly
from geo.models import Institution, Delegation, Agency, Entity


class DataGroup(models.Model):
    name = models.CharField(
        max_length=40, verbose_name="Nombre (devs)", blank=True, null=True)
    public_name = models.CharField(
        max_length=80, verbose_name="Nombre público")
    is_default = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default="lime")
    can_has_percent = models.BooleanField(
        default=False, verbose_name="Puede tener porcentajes")
    order = models.IntegerField(default=5)

    def delete(self, *args, **kwargs):
        from inai.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__file_control__data_group=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.public_name

    class Meta:
        verbose_name = "Grupo de datos solicitados"
        verbose_name_plural = "1.1 Grupos de datos solicitados"
        ordering = ['order']


class Collection(models.Model):
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE,
        verbose_name="Conjunto de datos")
    name = models.CharField(
        max_length=225, verbose_name="verbose_name_plural",
        help_text="Nombre del Modelo público (Meta.verbose_name_plural)")
    model_name = models.CharField(
        max_length=225,
        verbose_name="Nombre en Django",
        help_text="Nombre del modelo en Django (Meta.model_name)")
    snake_name = models.CharField(
        max_length=225,
        default="unknown",
        verbose_name="Nombre para distinguirlo en el código")
    app_label = models.CharField(
        max_length=40, verbose_name="App label", default="null")
    description = models.TextField(
        blank=True, null=True)
    open_insertion = models.BooleanField(
        default=False, verbose_name="Permitir inserción")
    cat_params = JSONField(
        default=dict, verbose_name="Parámetros para catálogo")

    def save(self, *args, **kwargs):
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.model_name)
        self.snake_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.app_label}-{self.model_name}"

    class Meta:
        verbose_name = "Modelo (Colección)"
        verbose_name_plural = "1.3 Modelos (Colecciones)"
        ordering = ['data_group', 'name']


def default_params_data_type():
    return {"name_pandas": ''}


class DataType(models.Model):
    name = models.CharField(max_length=50)
    public_name = models.CharField(max_length=225, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    addl_params = JSONField(
        default=default_params_data_type,
        verbose_name="Otras configuraciones")
    is_common = models.BooleanField(default=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de dato"
        verbose_name_plural = "2.CAT. Tipos de datos"


class ParameterGroup(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Agrupación de campos finales"
        verbose_name_plural = "1.2 Agrupaciones de campos finales"


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
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE)
    # data_group = models.IntegerField()
    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE,
        verbose_name="Entidad", blank=True, null=True)
    format_file = models.CharField(
        max_length=5,
        choices=FORMAT_CHOICES,
        null=True, blank=True)
    # file_format = models.IntegerField(blank=True, null=True)
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
    decode = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Codificación")
    # status_register = models.IntegerField(blank=True, null=True)
    status_register = models.ForeignKey(
        StatusControl, null=True, blank=True,
        verbose_name="Status de los registro de variables",
        on_delete=models.CASCADE)
    all_results = JSONField(blank=True, null=True)
    real_entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE,
        verbose_name="Proveedor real", blank=True, null=True)
    anomalies = models.ManyToManyField(
        Anomaly, verbose_name="Anomalías de los datos", blank=True)

    def save(self, *args, **kwargs):
        from inai.models import DataFile, TableFile
        final_real_entity = kwargs.get('real_entity', None)
        if final_real_entity != self.real_entity:
            data_files = DataFile.objects.filter(
                petition_file_control__file_control=self)
            table_files = TableFile.objects.filter(
                lap_sheet__sheet_file__data_file__petition_file_control__file_control=self)
            if final_real_entity is not None:
                data_files.update(entity=final_real_entity)
                table_files.update(entity=final_real_entity)
            else:
                data_files.update(entity=self.agency.entity)
                table_files.update(entity=self.agency.entity)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from inai.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__file_control=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def __str__(self):
        #all_agencies = Agency.objects.filter(
        #    petitions__file_controls__petition__agency=self).distinct()\
        #        .value_list("acronym", flat=True)
        return f"{self.id}. {self.name}"
        #return self.name

    class Meta:
        #unique_together = ["data_group", "name"]
        verbose_name = "Grupo de control de archivos"
        verbose_name_plural = "3.1 Grupos de control de archivos"
        db_table = "data_param_filecontrol"


class FinalField(models.Model):
    INCLUDED_CHOICES = (
        ("complete", "Completo"),
        ("complement", "Complementario"),
        ("wait", "En espera de inclusión; pausar"),
        ("invalid", "No válido, debe revisarse"),
    )
    MATCHING_CHOICES = (
        ("as_unique", "Como único"),
        ("in_list", "En la lista"),
        ("alternatives", "Nombres alternativos"),
    )

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE)
    parameter_group = models.ForeignKey(
        ParameterGroup, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(
        max_length=120, verbose_name="Nombre del campo en BD")
    verbose_name = models.CharField(
        max_length=255, verbose_name="Nombre público", blank=True, null=True)
    data_type = models.ForeignKey(
        DataType, 
        null=True, blank= True,
        on_delete=models.CASCADE,)
    addl_params = JSONField(
        blank=True, null=True, 
        verbose_name="Otras configuraciones", 
        help_text="Por ejemplo, max_length, null, blank, help_text, "
                     "django_field, así como otras que aparezcan")
    variations = JSONField(
        blank=True, null=True, 
        verbose_name="Otros posibles nombres (variaciones)",
        help_text="Nombres como pueden venir en las tablas de INAI",
        )
    regex_format = models.CharField(max_length=255, blank=True, null=True)
    is_required = models.BooleanField(
        default=False, verbose_name="Es indispensable para registrar fila")
    # included = models.BooleanField(
    #     verbose_name="valid", blank=True, null=True,
    #     help_text="¿La inserción lo incluye?")
    included_code = models.CharField(
        max_length=12, choices=INCLUDED_CHOICES, default="complement",
        verbose_name="valid")
    is_unique = models.BooleanField(
        default=False, help_text="Puede ser una llave única",
        verbose_name="Único")
    match_use = models.CharField(
        max_length=16, choices=MATCHING_CHOICES, blank=True, null=True,
        help_text="Uso en el match con catálogos")
    in_data_base = models.BooleanField(
        default=False, verbose_name="En DB",
        help_text="Ya está en la base de datos comprobado")
    verified = models.BooleanField(
        default=False, verbose_name="Verificado",
        help_text="Ricardo ya verificó que todos los parámetros están bien")
    is_common = models.BooleanField(
        default=False, verbose_name="Común")
    dashboard_hide = models.BooleanField(
        default=False,
        verbose_name="Oculta en dashboard",
        help_text="Ocultar en el dashboard (es complementaria o equivalente)")
    need_for_viz = models.BooleanField(
        default=False,
        verbose_name="Data viz",
        help_text="Se utiliza en indicadores de transparencia")

    def __str__(self):
        return "%s: %s (%s - %s)" % (
            self.verbose_name, self.parameter_group or "NA", 
            self.collection, self.name)

    class Meta:
        ordering = ["parameter_group", "-is_common", "verbose_name"]
        verbose_name = "Campo final"
        verbose_name_plural = "1.4 Campos finales (DB)"


class DictionaryFile(models.Model):
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, blank=True, null=True)
    # institution = models.ForeignKey(
    #     Institution, on_delete=models.CASCADE, blank=True, null=True)
    # delegation = models.ForeignKey(
    #     Delegation, on_delete=models.CASCADE, blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, on_delete=models.CASCADE, blank=True, null=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE)
    file = models.FileField(upload_to="dictionary_files")
    unique_field = models.ForeignKey(
        FinalField, on_delete=models.CASCADE, blank=True, null=True,
        related_name="dictionary_files")
    final_fields = models.ManyToManyField(
        FinalField, blank=True, verbose_name="Campos finales",
        related_name="m2m_dictionary_files")
    last_update = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        from django.utils import timezone
        self.last_update = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file} - {self.collection}"

    class Meta:
        verbose_name = "Catálogo para match"
        verbose_name_plural = "4.2 Diccionarios para match"


class CleanFunction(models.Model):
    READY_CHOICES = (
        ("ready_alone", "✳️Listo, solo"),
        ("ready", "Listo PREVIO"),
        ("ready 1", "1️⃣Listo 1"),
        ("ready 2", "2️⃣Listo 2"),
        ("ready CAT", "✅Listo CAT"),
        ("ready EXT", "✅Listo Ext"),
        ("not_ready", "❌Not ready"))

    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    priority = models.SmallIntegerField(
        default=5, 
        verbose_name="orden",
        help_text="Nivel de prioridad (ordenación)")
    for_all_data = models.BooleanField(
        default=False, verbose_name="All",
        help_text="Es una transformación para todo el archivo")
    restricted_field = models.ForeignKey(
        FinalField, blank=True, null=True,
        verbose_name="Campo exclusivo",
        help_text="Campo o variable al cual solo puede aplicarse",
        on_delete=models.CASCADE)
    addl_params = JSONField(
        blank=True, null=True,
        verbose_name="Otras configuraciones")
    ready_code = models.CharField(
        max_length=12, choices=READY_CHOICES, default="not_ready",
        verbose_name="Ready")
    column_type = models.ForeignKey(
        ColumnType, related_name="clean_functions",
        on_delete=models.CASCADE,
        verbose_name="Tipo de columna",
        blank=True, null=True)

    def __str__(self):
        return "%s (%s)" % (self.name, self.public_name)

    class Meta:
        ordering = ["priority", "public_name"]
        verbose_name = "Función de limpieza y transformación"
        verbose_name_plural = "2.CAT. Funciones de limpieza y transformación"


def default_params():
    return {}


class NameColumn (models.Model):
    name_in_data = models.TextField(
        verbose_name="Nombre de la columna real", blank=True, null=True)
    position_in_data = models.IntegerField(
        blank=True, null=True, verbose_name="idx")
    alternative_names = JSONField(
        blank=True, null=True,
        verbose_name="Nombres alternativos")
    # column_type = models.IntegerField(blank=True, null=True)
    column_type = models.ForeignKey(
        ColumnType, on_delete=models.CASCADE)
    # file_control = models.IntegerField(blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl,
        related_name="columns",
        blank=True, null=True,
        on_delete=models.CASCADE)
    # data_type = models.IntegerField(blank=True, null=True)
    data_type = models.ForeignKey(
        DataType,
        blank=True, null=True,
        on_delete=models.CASCADE)
    # final_field = models.IntegerField(blank=True, null=True)
    final_field = models.ForeignKey(
        FinalField,
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="name_columns")
    # clean_params = JSONField(
    #     blank=True, null=True, verbose_name="Parámetros de limpieza")
    required_row = models.BooleanField(default=False)
    parent_column = models.ForeignKey(
        "NameColumn", related_name="parents",
        verbose_name="Columna padre de la que derivó",
        blank=True, null=True, on_delete=models.CASCADE)
    child_column = models.ForeignKey(
        "NameColumn", related_name="childrens",
        verbose_name="Hijo resultado (junto a otras columnas)",
        blank=True, null=True, on_delete=models.CASCADE)
    seq = models.IntegerField(
        blank=True, null=True, verbose_name="order",
        help_text="Número consecutivo para ordenación en dashboard")
    last_update = models.DateTimeField(
        auto_now=True, verbose_name="Última actualización")

    def save(self, *args, **kwargs):
        from django.utils import timezone
        original = NameColumn.objects.filter(id=self.id).first()
        if original:
            if original.position_in_data is not None:
                if original.final_field != self.final_field:
                    self.last_update = timezone.now()
        super(NameColumn, self).save(*args, **kwargs)

    def __str__(self):
        return "%s-%s | %s" % (
            self.name_in_data, self.position_in_data, self.final_field or '?')

    class Meta:
        ordering = ["seq"]
        verbose_name = "Nombre de Columna"
        verbose_name_plural = "3.2 Nombres de Columnas"
        db_table = "data_param_namecolumn"


class Transformation(models.Model):

    # clean_function = models.IntegerField(blank=True, null=True)
    clean_function = models.ForeignKey(
        CleanFunction,
        on_delete=models.CASCADE,
        verbose_name="Función de limpieza o transformación")
    # file_control = models.IntegerField(blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl,
        related_name="file_transformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Grupo de control")
    # name_column = models.IntegerField(blank=True, null=True)
    name_column = models.ForeignKey(
        NameColumn,
        related_name="column_transformations",
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Columna")
    addl_params = JSONField(
        blank=True, null=True, default=default_params)

    def save(self, *args, **kwargs):
        from django.utils import timezone
        original = Transformation.objects.filter(id=self.id).first()
        if original:
            if original.name_column is not None:
                clean_function_changed = self.clean_function != original.clean_function
                addl_params_changed = self.addl_params != original.addl_params
                if clean_function_changed or addl_params_changed:
                    self.name_column.last_update = timezone.now()
                    self.name_column.save()
        super(Transformation, self).save(*args, **kwargs)

    def __str__(self):
        return "%s | %s" % (
            self.clean_function or '?', self.name_column or '?')

    class Meta:
        verbose_name = "Transformación a aplicar"
        verbose_name_plural = "4.1 Transformaciones a aplicar"
        db_table = "data_param_transformation"
