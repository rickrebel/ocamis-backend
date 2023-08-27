from django.db import models
from django.db.models import JSONField

from category.models import FileFormat


# Create your models here.
def default_list():
    return []


def default_dict():
    return {}


class Anomaly(models.Model):
    public_name = models.CharField(max_length=255,
        verbose_name="Nombre público")
    name = models.CharField(
        max_length=25, verbose_name="Nombre (devs)")
    is_public = models.BooleanField(default=True)
    description = models.TextField(
        blank=True, null=True, verbose_name="Descripción")
    icon = models.CharField(max_length=20, blank=True, null=True)
    is_calculated = models.BooleanField(default=False)
    order = models.IntegerField(default=5)
    color = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name="Color")

    def __str__(self):
        return self.public_name

    class Meta:
        verbose_name = "Anomalía en los datos"
        verbose_name_plural = "Anomalías en los datos"


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
        verbose_name = "Transparencia: Indicador"
        verbose_name_plural = "Transparencia: Indicadores"


class TransparencyLevel(models.Model):

    # transparency_index = models.IntegerField(blank=True, null=True)
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
    viz_params = JSONField(default=default_dict, blank=True)
    is_default = models.BooleanField(default=False)
    final_level = models.ForeignKey(
        "TransparencyLevel",
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
        verbose_name = "Transparencia: Nivel"
        verbose_name_plural = "Transparencia: Niveles"
