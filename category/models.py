from django.db import models
from django.db.models import JSONField


def default_list():
    return []


def default_dict():
    return {}


GROUP_CHOICES = (
    ("petition", "de Solicitud"),
    ("data", "Datos entregados"),
    ("complain", "Quejas - Revisiones"),
    ("register", "Registro de variables"),
    ("process", "Procesamiento de archivos (solo devs)"),
)


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
        verbose_name = "Status de control"
        verbose_name_plural = "Status de control (TODOS)"


class FileType(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    public_name = models.CharField(
        max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    has_data = models.BooleanField(default=False)
    is_original = models.BooleanField(default=False)
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
        verbose_name = "Tipo de archivo"
        verbose_name_plural = "Tipos de archivos"


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
        verbose_name = "Formato de archivos"
        verbose_name_plural = "Formatos de archivos"


class ColumnType(models.Model):
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=5)

    def __str__(self):
        return self.public_name

    class Meta:
        ordering = ['order']
        verbose_name = "Tipo de Columna"
        verbose_name_plural = "Tipos de columnas"


class NegativeReason(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Razón de negación de datos"
        verbose_name_plural = "Razones de negación de datos"


class InvalidReason(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Razón de invalidez de datos"
        verbose_name_plural = "Razones de invalidez de datos"


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
        verbose_name = "Fecha de corte"
        verbose_name_plural = "Fechas de corte"


