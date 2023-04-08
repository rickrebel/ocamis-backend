import uuid as uuid_lib

from django.db import models

from geo.models import Institution, Delegation, Entity


class Area(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    hex_hash = models.CharField(max_length=40, blank=True, null=True)
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
        return self.key or self.name

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"


class Doctor(models.Model):
    from geo.models import Institution, Delegation
    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    hex_hash = models.CharField(max_length=40, blank=True, null=True)
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
        return str(self.clave)


class Diagnosis(models.Model):

    uuid = models.UUIDField(
        primary_key=True, default=uuid_lib.uuid4, editable=False)
    hex_hash = models.CharField(max_length=40, blank=True, null=True)
    cie10 = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    motive = models.TextField(blank=True, null=True)
    aggregate_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE)
    is_aggregate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"

    def __str__(self):
        return self.cie10 or self.text or self.motive
