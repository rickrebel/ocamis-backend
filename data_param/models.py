#Para qué era esta importación?
from unicodedata import name
from django.db import models
from django.db.models import JSONField

from category.models import ColumnType, FileFormat, StatusControl
from transparency.models import Anomaly
from catalog.models import Entity


##Otros catalogos

class DataGroup(models.Model):
    name = models.CharField(
        max_length=40, verbose_name="Nombre (devs)", blank=True, null=True)
    public_name = models.CharField(
        max_length=80, verbose_name="Nombre público")
    is_default = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default="lime")
    can_has_percent = models.BooleanField(
        default=False, verbose_name="Puede tener porcentajes")

    def __str__(self):
        return self.public_name

    class Meta:
        verbose_name = "Grupo de datos solicitados"
        verbose_name_plural = "Grupos de datos solicitados"


class Collection(models.Model):
    name = models.CharField(
        max_length=225, verbose_name="verbose_name_plural",
        help_text="Nombre del Modelo público (Meta.verbose_name_plural)")
    model_name = models.CharField(
        max_length=225,
        verbose_name="Nombre en el código")
    description = models.TextField(
        blank=True, null=True)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE, 
        verbose_name="Conjunto de datos")

    def __str__(self):
        return f"{self.name} \n ({self.model_name})"

    class Meta:
        verbose_name = "Modelo (Tabla)"
        verbose_name_plural = "Modelos o Tablas"


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
        verbose_name_plural = "Tipos de datos"


class ParameterGroup(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Agrupación de campos finales"
        verbose_name_plural = "Agrupaciones de campos finales"


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
    # file_type = models.ForeignKey(
    #     FileType, on_delete=models.CASCADE,
    #     blank=True, null=True,)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE)
    # data_group = models.IntegerField()
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE,
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
    anomalies = models.ManyToManyField(
        Anomaly, verbose_name="Anomalías de los datos", blank=True)

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
        db_table = "data_param_filecontrol"


class FinalField(models.Model):
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
    is_required = models.BooleanField(
        default=False, verbose_name="Es indispensable para registrar fila")
    is_unique = models.BooleanField(
        default=False, help_text="Puede ser una llave única",
        verbose_name="Único")
    is_common = models.BooleanField(
        default=False, verbose_name="Es común")
    dashboard_hide = models.BooleanField(
        default=False,
        verbose_name="Oculta en dashboard",
        help_text="Ocultar en el dashboard (es complementaria o equivalente)")
    in_data_base = models.BooleanField(
        default=False, verbose_name="En DB", 
        help_text="Ya está en la base de datos comprobado")
    verified = models.BooleanField(
        default=False, verbose_name="Verificado", 
        help_text="Ricardo ya verificó que todos los parámetros están bien")
    need_for_viz = models.BooleanField(
        default=False,
        verbose_name="para data viz",
        help_text="Se utiliza en indicadores de transparencia")

    def __str__(self):
        return "%s: %s (%s - %s)" % (
            self.verbose_name, self.parameter_group or "NA", 
            self.collection, self.name)

    class Meta:
        ordering = ["parameter_group", "-is_common", "verbose_name"]
        verbose_name = "Campo final"
        verbose_name_plural = "Campos finales (en DB)"


class CleanFunction(models.Model):
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    priority = models.SmallIntegerField(
        default=5, 
        verbose_name="Prioridad",
        help_text="Nivel de prioridad (ordenación)")
    for_all_data = models.BooleanField(
        default=False, verbose_name="Es general",
        help_text="Es una transformación para toda la info")
    restricted_field = models.ForeignKey(
        FinalField, blank=True, null=True,
        verbose_name="Campo exclusivo",
        help_text="Campo o variable al cual solo puede aplicarse",
        on_delete=models.CASCADE)
    addl_params = JSONField(
        blank=True, null=True,
        verbose_name="Otras configuraciones")
    column_type = models.ForeignKey(
        ColumnType, related_name="col_type_functions",
        on_delete=models.CASCADE,
        verbose_name="Tipo de columna",
        blank=True, null=True)

    def __str__(self):
        return "%s (%s)" % (self.name, self.public_name)

    class Meta:
        ordering = ["priority", "public_name"]
        verbose_name = "Función de limpieza y transformación"
        verbose_name_plural = "Funciones de limpieza y transformación"


def default_params():
    return {}


class NameColumn (models.Model):
    name_in_data = models.TextField(
        verbose_name="Nombre de la columna real", blank=True, null=True)
    position_in_data = models.IntegerField(
        blank=True, null=True, verbose_name="idx")
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
    # collection = models.IntegerField(blank=True, null=True)
    collection = models.ForeignKey(
        Collection,
        blank=True, null=True,
        on_delete=models.CASCADE)
    # final_field = models.IntegerField(blank=True, null=True)
    final_field = models.ForeignKey(
        FinalField,
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="name_columns")
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

    class Meta:
        verbose_name = "Transformación a aplicar"
        verbose_name_plural = "Transformaciones a aplicar"
        db_table = "data_param_transformation"

