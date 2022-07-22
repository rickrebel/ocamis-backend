#Para qué era esta importación?
from unicodedata import name
from django.db import models
from django.contrib.postgres.fields import JSONField
##Otros catalogos


class GroupData(models.Model):
    name = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)
    can_has_percent = models.BooleanField(
        default=False, verbose_name="Puede tener porcentajes")

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
        verbose_name = u"Grupo de Parametros"
        verbose_name_plural = u"Grupos de Parametros"


class Collection(models.Model):
    name = models.CharField(max_length=225)
    model_name = models.CharField(
        max_length=225, verbose_name="Nombre en el código")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Modelo (Tabla)"
        verbose_name_plural = u"Modelos o Tablas"


class TypeData(models.Model):
    def default_params_type_data():
        return {"name_pandas": ''}
    name = models.CharField(max_length=225)
    description =  models.TextField(blank=True, null=True)
    addl_params = JSONField(
        default=default_params_type_data,
        verbose_name="Otras configuraciones")
    is_common = models.BooleanField(default=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Tipo de dato"
        verbose_name_plural = u"Tipos de datos"


class FinalField(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE)
    name = models.CharField(max_length=120, blank=True, null=True)
    verbose_name = models.TextField(blank=True, null=True)
    type_data = models.ForeignKey(
        TypeData, 
        null=True, blank= True,
        on_delete=models.CASCADE,)
    addl_params = JSONField(
        blank=True, null=True, verbose_name="Otras configuraciones")

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
    variations = JSONField(
        blank=True, null=True, verbose_name="Variaciones comunes del nombre")
    almost_requiered = models.BooleanField(
        default=False, verbose_name="Es casi indispensable")
    is_common = models.BooleanField(
        default=False, verbose_name="Es un parámetro común")
    final_field = models.ForeignKey(
        FinalField, 
        null=True, blank= True,
        on_delete=models.CASCADE,)
    is_verified = models.BooleanField(default=False)
    addl_params = JSONField(
        blank=True, null=True,
        verbose_name="Otras configuraciones")

    def __str__(self):
        return "%s, %s" % (self.name, self.group_parameter)

    class Meta:
        verbose_name = u"Parametro"
        verbose_name_plural = u"Parametros"


class CleanFunction(models.Model):
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    pririty = models.SmallIntegerField(
        default=5, verbose_name="Nivel de prioridad (5 niveles)")
    for_all_data = models.BooleanField(
        default=False, verbose_name="Es una tranformación para toda la info")
    restricted_field = models.ForeignKey(
        FinalField, blank=True, null=True,
        verbose_name="Campo final al cual solo puede aplicarse",
        on_delete=models.CASCADE)

    def __str__(self):
        return "%s (%s)" (self.name, self.public_name)

    class Meta:
        verbose_name = u"Función de Transformación"
        verbose_name_plural = u"Funciones de transformación"
