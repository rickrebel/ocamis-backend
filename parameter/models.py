from unicodedata import name
from django.db import models

# Create your models here.


from django.db import models
from django.contrib.postgres.fields import JSONField


##Otros catalogos

class GroupData(models.Model):
    name = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo de datos"
        verbose_name_plural = u"Grupos de datos"


class GroupParameter(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    group_data = models.ForeignKey(
        GroupData, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo Parametro"
        verbose_name_plural = u"Grupo Parametros"

class Collection(models.Model):
    name = models.CharField(max_length=225)
    model_name = models.CharField(max_length=225)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Coleccion"
        verbose_name_plural = u"Colecciones"

class TypeData(models.Model):
    name = models.CharField(max_length=225)
    description =  models.TextField(blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    is_common = models.BooleanField(default=True)
    order = models.IntegerField() ##

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Tipo de dato"
        verbose_name_plural = u"Tipos de datos"


class FinalField(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    verbose_name = models.TextField(blank=True, null=True)
    type_data = models.ForeignKey(
        TypeData, 
        null=True, blank= True,
        on_delete=models.CASCADE,)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Documento final"
        verbose_name_plural = u"Documentos finales"


class Parameter(models.Model):
    group_parameter = models.ForeignKey(
        GroupParameter, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    default_name = models.CharField(max_length=255)
    variations = JSONField(blank=True, null= True)
    almost_requiered = models.BooleanField(default=False)
    is_common = models.BooleanField(default=False)
    final_field = models.ForeignKey(
        FinalField, 
        null=True, blank= True,
        on_delete=models.CASCADE,)
    is_verified = models.BooleanField(default=False)
    addl_params = JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Parametro"
        verbose_name_plural = u"Parametros"






    


