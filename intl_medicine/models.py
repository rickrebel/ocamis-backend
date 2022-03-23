from django.db import models

# Create your models here.

from medicine.models import Component


class InternatinalTerapeticGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(
        verbose_name="Sin equivalente", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupo Terapeútico Internacional"
        verbose_name_plural = "Grupos Terapeúticos Internacionales"


class InternationalMedicine(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    original_name = models.CharField(
        null=True, blank=True,
        max_length=255, verbose_name="Nombre original (inglés)")
    component = models.OneToOneField(
        Component, verbose_name="Componente asociado",
        blank=True, null=True, on_delete=models.CASCADE)
    without_equal = models.BooleanField(
        default=False, verbose_name="Sin equivalente")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Medicamento Internacional"
        verbose_name_plural = "Medicamentos Internacionales"


class ClasificationSource(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre de la Fuente")
    instituciones = models.TextField(
        null=True, blank=True, verbose_name="Instituciones participante")
    notes = models.TextField(
        verbose_name="Otras notas", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fuente de clasificación"
        verbose_name_plural = "Fuentes de clasificación"


class PriorizedMedSource(models.Model):
    international_medicine = models.ForeignKey(
        InternationalMedicine, on_delete=models.CASCADE)
    clasification_source = models.ForeignKey(
        ClasificationSource, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (
            self.international_medicine, self.clasification_source)

    class Meta:
        verbose_name = "Priorización según fuentes internacionales"
        verbose_name_plural = "Priorizaciones según fuentes internacionales"
