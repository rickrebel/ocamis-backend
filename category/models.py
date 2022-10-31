from distutils import extension
from django.db import models
from django.contrib.postgres.fields import JSONField


GROUP_CHOICES = (
    ("petition", "de Solicitud"),
    ("data", "Datos entregados"),
    ("complain", "Quejas - Revisiones"),
    ("process", "Procesamiento de archivos (solo devs)"),
    ("register", "Registro de variables (solo devs)"),
)

def default_list():
    return []

def default_dict():
    return {}


class StatusControl(models.Model):
    group = models.CharField(
        max_length=10, choices=GROUP_CHOICES, 
        verbose_name="grupo de status", default="petition")
    name = models.CharField(max_length=120)
    public_name = models.CharField(max_length=255)
    color = models.CharField(
        max_length=30, blank=True, null=True,
        help_text="https://vuetifyjs.com/en/styles/colors/")
    icon = models.CharField(max_length=20, blank=True, null=True)
    order = models.IntegerField(default=4)
    description = models.TextField(blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s - %s"  % (self.group, self.public_name)

    class Meta:
        ordering = ["group", "order"]
        verbose_name = u"Status de control"
        verbose_name_plural = u"Status de control (TODOS)"


class FileType(models.Model):
    name = models.CharField(max_length=255)
    public_name = models.CharField(
        max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    has_data = models.BooleanField(default= False)
    is_original = models.BooleanField(default= False)
    order = models.IntegerField(default=15)
    color = models.CharField(max_length=20, blank=True, null=True)
    group = models.CharField(
        max_length=10, choices=GROUP_CHOICES, 
        verbose_name="grupo", default="petition")
    #default_format = models.ForeignKey(
    #    FormatFile, on_delete=models.CASCADE, blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order"]
        verbose_name = u"Tipo de archivo"
        verbose_name_plural = u"Tipos de archivos"


class FileFormat(models.Model):

    short_name = models.CharField(max_length=20)
    public_name = models.CharField(max_length=80)
    suffixes = JSONField(
        default=default_list, blank=True, null=True,
        verbose_name="extensiones")
    readable = models.BooleanField(verbose_name="es legible por máquinas")
    addl_params = JSONField(default=default_dict, blank=True)
    order = models.IntegerField(default=10, blank=True)

    def __str__(self):
        return self.public_name

    class Meta:
        verbose_name = u"Formato de archivos"
        verbose_name_plural = u"Formatos de archivos"


class ColumnType(models.Model):
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=5)

    def __str__(self):
        return self.public_name

    class Meta:
        ordering = ['order']
        verbose_name = u"Tipo de Columna"
        verbose_name_plural = u"Tipos de columnas"


class NegativeReason(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Razón de negación de datos"
        verbose_name_plural = u"Razones de negación de datos"


class InvalidReason(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Razón de invalidez de datos"
        verbose_name_plural = u"Razones de invalidez de datos"


class DateBreak(models.Model):
    name = models.CharField(max_length=50)
    group = models.CharField(
        max_length=10, choices=GROUP_CHOICES, 
        verbose_name="grupo", default="petition")
    public_name = models.CharField(max_length=120)
    order = models.IntegerField(default=5)
    break_params = JSONField(blank=True, null=True)

    def __str__(self):
        return "%s - %s"  % (self.group, self.public_name)

    class Meta:
        ordering = ["order"]
        verbose_name = u"Fecha de corte"
        verbose_name_plural = u"Fechas de corte"


class Anomaly(models.Model):
    public_name = models.CharField(max_length=255, 
        verbose_name=u"Nombre público")
    name = models.CharField(
        max_length=25, verbose_name=u"Nombre (devs)")
    is_public = models.BooleanField(default=True)
    description = models.TextField(
        blank=True, null=True, verbose_name=u"Descripción")
    icon = models.CharField(max_length=20, blank=True, null=True)
    is_calculated = models.BooleanField(default=False)
    order = models.IntegerField(default=5)
    color = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name=u"Color")

    def __str__(self):
        return self.public_name

    class Meta:
        verbose_name = u"Anomalía en los datos"
        verbose_name_plural = u"Anomalías en los datos"


class TransparencyIndex(models.Model):
    short_name = models.CharField(max_length=20)
    public_name = models.CharField(max_length=80)
    description = models.TextField(blank=True, null=True)
    scheme_color = models.CharField(
        max_length=90, blank=True, null=True, verbose_name="Esquema de color")
    viz_params = JSONField(default=default_dict, blank=True)
    order_viz = models.IntegerField(
        default=-3, verbose_name="Orden en visualización")

    def __str__(self):
        return f"{self.public_name}\n ({self.short_name})"

    class Meta:
        ordering = ["order_viz"]
        verbose_name = u"Transparencia: Indicador"
        verbose_name_plural = u"Transparencia: Indicadores"


class TransparencyLevel(models.Model):

    transparency_index = models.ForeignKey(
        TransparencyIndex, 
        verbose_name="Indicador de Transparencia",
        related_name="levels",
        on_delete=models.CASCADE)
    short_name = models.CharField(max_length=20)
    public_name = models.CharField(max_length=80)
    value = models.IntegerField(default=0,
        help_text="Para ordenar y decidier según menor")
    description = models.TextField(blank=True, null=True)
    anomalies = models.ManyToManyField(
        Anomaly, blank=True, verbose_name="Anomalías relacionadas")
    file_formats = models.ManyToManyField(
        FileFormat, blank=True, verbose_name="Formatos de archivo")
    other_conditions = JSONField(default=default_list, blank=True)
    final_level = models.ForeignKey("TransparencyLevel", 
        verbose_name="Concentrado destino", 
        help_text="Si existe, se va a ese nivel de indicador principal",
        blank=True, null=True, on_delete=models.CASCADE)
    color = models.CharField(max_length=20, blank=True, null=True)
    order_viz = models.IntegerField(
        default=-3, verbose_name="Orden en visualización")
    value_ctrls = models.IntegerField(
        default=-3, verbose_name="Priorización entre controles")
    value_pets = models.IntegerField(
        default=-3, verbose_name="Priorización entre solicitudes")

    @property
    def index_short_name(self):
        return self.transparency_index.short_name

    def __str__(self):
        return f"{self.transparency_index} - {self.public_name}"

    class Meta:
        ordering = ["transparency_index__order_viz", "-order_viz"]
        verbose_name = u"Transparencia: Nivel"
        verbose_name_plural = u"Transparencia: Niveles"
