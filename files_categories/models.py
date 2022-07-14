from distutils import extension
from django.db import models

# Create your models here.


class StatusProcessing(models.Model):
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=20, blank=True, null=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Estado del proceso"
        verbose_name_plural = u"Estados de procesos"

class TypeFile(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    has_data = models.BooleanField(default= False)
    is_original = models.BooleanField(default= False)
    order = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Tipo de documento"
        verbose_name_plural = u"Tipos de documentos"


class FormatFile(models.Model):
    name = models.CharField(max_length=255)
    extension = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)
    has_data = models.BooleanField(default=True)
    icon = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Formato de documento"
        verbose_name_plural = u"Formato de documentos"



