#Para qué era esta importación?
from unicodedata import name
from django.db import models
from django.contrib.postgres.fields import JSONField

##Otros catalogos

class DataGroup(models.Model):
    name = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)
    can_has_percent = models.BooleanField(
        default=False, verbose_name="Puede tener porcentajes")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo de datos"
        verbose_name_plural = u"Grupos de datos"


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
        return self.name

    class Meta:
        verbose_name = u"Modelo (Tabla)"
        verbose_name_plural = u"Modelos o Tablas"


class DataType(models.Model):
    def default_params_data_type():
        return {"name_pandas": ''}
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
        verbose_name = u"Tipo de dato"
        verbose_name_plural = u"Tipos de datos"


class FinalField(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=120, verbose_name="Nombre del campo en BD")
    verbose_name = models.CharField(
        max_length=255, blank=True, null=True)
    data_type = models.ForeignKey(
        DataType, 
        null=True, blank= True,
        on_delete=models.CASCADE,)
    addl_params = JSONField(
        blank=True, null=True, 
        verbose_name="Otras configuraciones", 
        help_text="Por ejemplo, max_length, null, blank, help_text,"
            " así como otras configuraciones que se nos vayan ocurriendo")
    variations = JSONField(
        blank=True, null=True, 
        verbose_name="Otros posibles nombres (variaciones)",
        help_text="Nombres como pueden venir en las tablas de INAI",
        )
    requiered = models.BooleanField(
        default=False, verbose_name="Es indispensable para registrar fila")
    is_common = models.BooleanField(
        default=False, verbose_name="Es una variable muy común")
    dashboard_hide = models.BooleanField(
        default=False,
        verbose_name="Oculta en dashboard",
        help_text="Ocultar en el dashboard (es complementaria o equivalente)")
    in_data_base = models.BooleanField(
        default=False, verbose_name="Verificado (solo devs)", 
        help_text="Ya está en la base de datos comprobado")
    verified = models.BooleanField(
        default=False, verbose_name="Verificado (solo rick)", 
        help_text="Ricardo ya verificó que todos los parámetros están bien")

    def __str__(self):
        return "%s - %s" % (self.collection, self.name)

    class Meta:
        ordering = ["collection", "name"]
        verbose_name = u"Campo final"
        verbose_name_plural = u"Campos finales (en DB)"


class CleanFunction(models.Model):
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    priority = models.SmallIntegerField(
        default=5, verbose_name="Nivel de prioridad (5 niveles)")
    for_all_data = models.BooleanField(
        default=False, verbose_name="Es una transformación para toda la info")
    restricted_field = models.ForeignKey(
        FinalField, blank=True, null=True,
        verbose_name="Campo final al cual solo puede aplicarse",
        on_delete=models.CASCADE)
    addl_params = JSONField(
        blank=True, null=True,
        verbose_name="Otras configuraciones")

    def __str__(self):
        return "%s (%s)" % (self.name, self.public_name)

    class Meta:
        verbose_name = u"Función de limpieza y transformación"
        verbose_name_plural = u"Funciones de limpieza y transformación"

""" class GroupParameter(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    data_group = models.ForeignKey(
        DataGroup, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Grupo de Parametros"
        verbose_name_plural = u"Grupos de Parametros" """


""" class Parameter(models.Model):
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
        verbose_name_plural = u"Parametros" """
