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

class StatusControl(models.Model):
    group = models.CharField(
        max_length=10, choices=GROUP_CHOICES, 
        verbose_name="grupo de status", default="petition")
    name = models.CharField(max_length=120)
    public_name = models.CharField(max_length=255)
    color = models.CharField(
        max_length=20, blank=True, null=True,
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


"""class FormatFile(models.Model):
    name = models.CharField(max_length=255)
    extension = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)
    has_data = models.NullBooleanField(
        verbose_name="Tiene datos procesables")
    icon = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Formato de documento"
        verbose_name_plural = u"Formato de documentos" """
