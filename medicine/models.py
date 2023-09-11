# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Group(models.Model):
    name = models.CharField(max_length=255)
    number = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name.strip() or str(self.number)

    class Meta:
        verbose_name = "Grupo Terapeútico"
        verbose_name_plural = "1. Grupos Terapeúticos"
        db_table = 'medicine_group'


class Component(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    medicine_type = models.CharField(
        max_length=255, blank=True, null=True)
    alias = models.CharField(
        max_length=255,
        verbose_name="Nombres alternativos y comerciales",
        blank=True, null=True)
    presentation_count = models.IntegerField(default=1)
    frequency = models.IntegerField(default=0, blank=True, null=True)

    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)
    presentations_raw = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)
    is_relevant = models.BooleanField(default=True)
    priority = models.IntegerField(default=10)

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Componente"
        verbose_name_plural = "2. Componentes"
        ordering = ["priority", "name"]
        db_table = 'medicine_component'


class PresentationType(models.Model):
    name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    presentation_count = models.IntegerField(default=0)
    agrupated_in = models.ForeignKey(
        "PresentationType", blank=True, null=True, on_delete=models.CASCADE)
    # agrupated_in = models.IntegerField(blank=True, null=True)
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
        verbose_name_plural = "0. Tipos de presentación"
        ordering = ["name"]
        db_table = 'medicine_presentationtype'


class Presentation(models.Model):
    component = models.ForeignKey(
        Component, related_name="presentations", on_delete=models.CASCADE)
    presentation_type = models.ForeignKey(
        PresentationType, blank=True, null=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    presentation_type_raw = models.CharField(
        max_length=255, blank=True, null=True)
    # Según yo se tendría que borrar...
    clave = models.CharField(max_length=20, blank=True, null=True)
    official_name = models.TextField(blank=True, null=True)
    official_attributes = models.TextField(blank=True, null=True)
    short_attributes = models.TextField(blank=True, null=True)
    origen_cvmei = models.BooleanField(default=False)

    group = models.ForeignKey(
        Group, blank=True, null=True,
        on_delete=models.CASCADE, related_name="prev_presentations")
    groups = models.ManyToManyField(
        Group, related_name="presentations", blank=True)

    def __str__(self):
        return " ".join([self.component.name, self.short_attributes or ""])

    class Meta:
        verbose_name = "Presentación del componente"
        verbose_name_plural = "3. Presentaciones del componente"
        db_table = 'medicine_presentation'


class Container(models.Model):
    presentation = models.ForeignKey(
        Presentation, related_name="containers", blank=True, null=True,
        on_delete=models.CASCADE)
    name = models.TextField()
    key = models.CharField(verbose_name="Clave", max_length=20)
    key2 = models.CharField(
        max_length=20, verbose_name="Clave sin puntos",
        blank=True, null=True,
    )
    is_current = models.BooleanField(default=True)
    short_name = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)

    def __str__(self):
        return "%s - %s - %s" % (
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
        verbose_name_plural = "4. Recipientes (Contenedores)"
        db_table = 'medicine_container'
