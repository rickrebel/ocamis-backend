# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
#from report.models import Supply


@python_2_unicode_compatible
class Group(models.Model):
    name = models.CharField(max_length=255)
    number = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name.strip() or str(self.number)

    class Meta:
        verbose_name = "Grupo Terapeútico"
        verbose_name_plural = "Grupos Terapeúticos"
        db_table = u'desabasto_group'


@python_2_unicode_compatible
class Component(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(
        max_length=255,
        verbose_name=u"Nombres alternativos y comerciales",
        blank=True, null=True)
    presentation_count = models.IntegerField(default=1)
    frequency = models.IntegerField(default=0, blank=True, null=True)

    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)
    #group = models.IntegerField(blank=True, null=True)
    presentations_raw = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)
    is_relevant = models.BooleanField(default=True)

    is_vaccine = models.BooleanField(default=False)

    @property
    def len_short_name(self):
        if not self.short_name:
            return 0
        return len(self.short_name)

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = self.name
        super(Component, self).save(*args, **kwargs)

    """def update_frecuency(self):
        self.frequency = Supply.objects\
            .filter(component=self).distinct().count()
        self.save()"""

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Componente"
        verbose_name_plural = "Componentes"
        db_table = u'desabasto_component'


@python_2_unicode_compatible
class PresentationType(models.Model):
    name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    presentation_count = models.IntegerField(default=0)
    agrupated_in = models.ForeignKey(
        "PresentationType", blank=True, null=True, on_delete=models.CASCADE)
    #agrupated_in = models.IntegerField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(PresentationType, self).save(*args, **kwargs)

        if self.agrupated_in:
            Presentation.objects.filter(presentation_type=self)\
                .update(presentation_type=self.agrupated_in)

            self.delete()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de presentación"
        verbose_name_plural = "Tipos de presentación"
        ordering = ["name"]
        db_table = u'desabasto_presentationtype'


@python_2_unicode_compatible
class Presentation(models.Model):
    component = models.ForeignKey(
        Component, related_name=u"presentations", on_delete=models.CASCADE)
    #component = models.IntegerField()
    presentation_type = models.ForeignKey(
        PresentationType, blank=True, null=True, on_delete=models.CASCADE)
    #presentation_type = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    presentation_type_raw = models.CharField(
        max_length=255, blank=True, null=True)

    clave = models.CharField(max_length=20, blank=True, null=True)
    official_name = models.TextField(blank=True, null=True)
    official_attributes = models.TextField(blank=True, null=True)
    short_attributes = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)

    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)
    #group = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return u" ".join([self.component.name, self.short_attributes or ""])

    class Meta:
        verbose_name = "Presentación del componente"
        verbose_name_plural = "Presentaciones del componente"
        db_table = u'desabasto_presentation'


@python_2_unicode_compatible
class Container(models.Model):
    presentation = models.ForeignKey(
        Presentation, related_name=u"containers", blank=True, null=True,
        on_delete=models.CASCADE)
    #presentation = models.IntegerField(blank=True, null=True)
    name = models.TextField()
    key = models.CharField(verbose_name=u"Clave", max_length=20)
    key2 = models.CharField(
        max_length=20, verbose_name=u"Clave sin puntos",
        blank=True, null=True,
    )
    is_current = models.NullBooleanField(default=True)
    short_name = models.TextField(blank=True, null=True)

    origen_cvmei = models.NullBooleanField(default=False)

    def __str__(self):
        return u"%s - %s - %s" % (
            self.presentation.component.name,
            self.presentation.presentation_type_raw,
            self.name)

    def save(self, *args, **kwargs):
        if self.key:
            self.key2 = self.key.replace(".", "")
        super(Container, self).save(*args, **kwargs)
        if self.key[:4] == "020.":
            Component.objects.filter(presentations=self.presentation)\
                .update(is_vaccine=True)

    class Meta:
        verbose_name = "Recipiente (Contenedor)"
        verbose_name_plural = "Recipientes (Contenedores)"
        db_table = u'desabasto_container'
