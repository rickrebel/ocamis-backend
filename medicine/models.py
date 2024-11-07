# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from category.models import StatusControl


class Source(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    institution = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fuente de catálogo"
        verbose_name_plural = "Fuentes de catálogo"


class Group(models.Model):
    name = models.CharField(max_length=255)
    unidecode_name = models.CharField(max_length=255, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    need_survey = models.BooleanField(default=True)

    def __str__(self):
        return self.name.strip() or str(self.number)
    
    def save(self, *args, **kwargs):
        from unidecode import unidecode
        if not self.unidecode_name:
            self.unidecode_name = unidecode(self.name).lower().strip()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Grupo Terapeútico"
        verbose_name_plural = "1. Grupos Terapeúticos"
        ordering = ["number"]
        db_table = 'medicine_group'


class Component(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    medicine_type = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(
        max_length=255,
        verbose_name="Nombres alternativos y comerciales",
        blank=True, null=True)
    alternative_names = models.JSONField(
        default=list, blank=True, null=True, verbose_name="Otros nombres")
    presentation_count = models.IntegerField(default=1)
    frequency = models.IntegerField(default=0, blank=True, null=True)
    # TODO RICK: Eliminar este campo:
    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.CASCADE)
    groups = models.ManyToManyField(
        Group, related_name="components", blank=True)
    presentations_raw = models.TextField(blank=True, null=True)

    origen_cvmei = models.BooleanField(default=False)
    is_relevant = models.BooleanField(default=True)
    priority = models.IntegerField(default=10)
    description = models.TextField(blank=True, null=True)
    # Datos del compendio:
    generalities = models.TextField(
        blank=True, null=True, verbose_name="Generalidades")
    pregnancy_risks = models.TextField(
        blank=True, null=True, verbose_name="Riesgos en el embarazo")
    adverse_effects = models.TextField(
        blank=True, null=True, verbose_name="Efectos adversos")
    contraindications = models.TextField(
        blank=True, null=True,
        verbose_name="Contraindicaciones y precauciones")
    interactions = models.TextField(
        blank=True, null=True, verbose_name="Interacciones")
    groups_count = models.IntegerField(default=0, verbose_name="Gpos")
    groups_pc_count = models.IntegerField(default=0, verbose_name="Gpos. priori")
    presentations_count = models.IntegerField(default=0, verbose_name="Pres.")
    containers_count = models.IntegerField(default=0, verbose_name="Cont.")
    is_vaccine = models.BooleanField(default=False)

    notes = models.TextField(blank=True, null=True)
    source_data = models.JSONField(default=dict, blank=True, null=True)
    status_review = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE,
        related_name="components_review")
    status_final = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE,
        related_name="components_final")

    @property
    def containers(self):
        return Container.objects.filter(presentation__component=self)

    @property
    def len_short_name(self):
        if not self.short_name:
            return 0
        return len(self.short_name)

    def count(self):
        from intl_medicine.models import PrioritizedComponent
        pcs = PrioritizedComponent.objects.filter(
            component=self, group_answer__respondent__isnull=True)
        self.groups_pc_count = pcs.count()
        presentations = self.presentations.all()
        self.presentations_count = presentations.count()
        groups = Group.objects.filter(presentations__in=presentations)
        self.groups_count = groups.count()
        self.containers_count = self.containers.count()
        self.save()

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
            Presentation.objects.filter(presentation_type=self) \
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
    content_title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    presentation_type_raw = models.CharField(
        max_length=255, blank=True, null=True)
    indications = models.TextField(
        blank=True, null=True, verbose_name="Indicaciones")
    way = models.TextField(
        blank=True, null=True, verbose_name="Vía de administración")
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

    source_data = models.JSONField(default=dict, blank=True, null=True)
    status_review = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE,
        related_name="presentations_review")
    status_final = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE,
        related_name="presentations_final")

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
    name = models.TextField(blank=True, null=True)
    key = models.CharField(verbose_name="Clave", max_length=20)
    key2 = models.CharField(
        max_length=20, verbose_name="Clave sin puntos",
        blank=True, null=True)
    is_current = models.BooleanField(default=True)
    short_name = models.TextField(blank=True, null=True)
    origen_cvmei = models.BooleanField(default=False)

    source_data = models.JSONField(default=dict, blank=True, null=True)
    status_review = models.ForeignKey(
        StatusControl, blank=True, null=True, on_delete=models.CASCADE,
        related_name="containers_review")

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
            Component.objects.filter(presentations=self.presentation) \
                .update(is_vaccine=True)

    class Meta:
        verbose_name = "Recipiente (Contenedor)"
        verbose_name_plural = "4. Recipientes (Contenedores)"
        db_table = 'medicine_container'


class ViewMedicine(models.Model):
    container_id = models.IntegerField(primary_key=True)
    key = models.CharField(max_length=20)
    key2 = models.CharField(max_length=20)
    container_name = models.TextField()
    presentation_id = models.IntegerField()
    presentation_name = models.TextField()
    component_id = models.IntegerField()
    component_name = models.TextField()
    priority = models.IntegerField()

    def __str__(self):
        return f"{self.component_name} - {self.presentation_name} - {self.container_name}"

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "5. Medicamentos"
        db_table = 'view_medicine'
        managed = False
