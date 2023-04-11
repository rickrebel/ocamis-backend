import uuid as uuid_lib
import hashlib

from django.db import models

from geo.models import Institution, Delegation, Entity, Typology, CLUES
from medicine.models import Component, Presentation, Container


class MedicalUnit(models.Model):
    hex_hash = models.CharField(max_length=32, primary_key=True)
    entity = models.ForeignKey(
        Entity, verbose_name="Entity", on_delete=models.CASCADE)
    delegation = models.ForeignKey(
        Delegation, verbose_name="Delegación",
        on_delete=models.CASCADE, blank=True, null=True)
    clues = models.ForeignKey(
        CLUES, verbose_name="CLUES", on_delete=models.CASCADE,
        blank=True, null=True)
    delegation_name = models.CharField(
        max_length=255, blank=True, null=True)
    state_name = models.CharField(
        max_length=255, blank=True, null=True)
    jurisdiction_key = models.CharField(
        max_length=50, blank=True, null=True)
    name = models.CharField(
        max_length=255, blank=True, null=True)
    attention_level = models.CharField(
        max_length=80, blank=True, null=True)
    clues_key = models.CharField(
        max_length=12, blank=True, null=True)
    own_key = models.CharField(
        max_length=255, blank=True, null=True)
    key_issste = models.CharField(
        max_length=12, blank=True, null=True)
    typology_key = models.CharField(
        max_length=18, blank=True, null=True)
    typology_name = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return self.hex_hash

    class Meta:
        verbose_name = "Unidad Médica"
        verbose_name_plural = "Unidades Médicas"


class Area(models.Model):

    hex_hash = models.CharField(max_length=32, primary_key=True)
    # hex_hash = models.CharField(max_length=40, blank=True, null=True)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    # institution = models.ForeignKey(
    #     Institution, on_delete=models.CASCADE)
    # delegation = models.ForeignKey(
    #     Delegation, null=True, blank=True, on_delete=models.CASCADE)
    key = models.CharField(
        max_length=255, verbose_name="Clave del área",
        blank=True, null=True)
    name = models.TextField(
        verbose_name="Nombre del área",
        blank=True, null=True)
    description = models.TextField(
        verbose_name="Descripción del área",
        blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)

    def __str__(self):
        return self.hex_hash

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"


class Doctor(models.Model):
    from geo.models import Institution, Delegation

    hex_hash = models.CharField(max_length=32, primary_key=True)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    # institution = models.ForeignKey(
    #     Institution, on_delete=models.CASCADE)
    # delegation = models.ForeignKey(
    #     Delegation, null=True, blank=True, on_delete=models.CASCADE)
    clave = models.CharField(max_length=30, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    medical_speciality = models.CharField(max_length=255, blank=True, null=True)
    professional_license = models.CharField(max_length=20, blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctores"

    def __str__(self):
        return self.hex_hash


class Diagnosis(models.Model):

    hex_hash = models.CharField(max_length=32, primary_key=True)
    cie10 = models.CharField(max_length=40, blank=True, null=True)
    own_key = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    motive = models.TextField(blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"

    def __str__(self):
        return self.hex_hash


class Medicament(models.Model):

    hex_hash = models.CharField(max_length=32, primary_key=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, blank=True, null=True,
        help_text="ent")
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, blank=True, null=True)
    presentation = models.ForeignKey(
        Presentation, on_delete=models.CASCADE, blank=True, null=True)
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, blank=True, null=True)
    key2 = models.CharField(
        max_length=20, help_text="key2")
    own_key2 = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="own")
    medicine_type = models.CharField(
        max_length=90, blank=True, null=True,
        help_text="mt")
    component_name = models.TextField(
        blank=True, null=True, help_text="comp")
    presentation_type = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="pt")
    presentation_description = models.TextField(
        blank=True, null=True, help_text="pres")
    container_name = models.TextField(
        blank=True, null=True, help_text="cont")

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"

    def __str__(self):
        return self.hex_hash
