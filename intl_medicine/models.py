from django.db import models

from medicine.models import Component, Group
from django.contrib.auth.models import User


class Respondent(models.Model):
    first_name = models.CharField(max_length=255, verbose_name="Nombre")
    last_name = models.CharField(
        max_length=255, verbose_name="Apellido", blank=True, null=True)
    email = models.EmailField(verbose_name="Correo electrónico")
    token = models.CharField(max_length=255, verbose_name="Token")
    institution = models.CharField(
        max_length=255, verbose_name="Institución", blank=True, null=True)
    position = models.CharField(
        max_length=255, verbose_name="Cargo", blank=True, null=True)
    recognition = models.BooleanField(
        blank=True, null=True, verbose_name="Mostrar nombre",
        help_text="Permite mostrar el nombre del encuestado")
    # completed_groups = models.ManyToManyField(
    #     Group, verbose_name="Grupos completados", blank=True)

    def get_next_group(self):
        group_ids = self.responses.values_list("group_id", flat=True)
        return Group.objects.exclude(id__in=group_ids).order_by("?").first()

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}"
        return f"{full_name} - {self.institution}"

    class Meta:
        verbose_name = "Encuestado"
        verbose_name_plural = "Encuestados"


class GroupAnswer(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="responses")
    respondent = models.ForeignKey(
        Respondent, on_delete=models.CASCADE,
        related_name="responses", blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    date_started = models.DateTimeField(blank=True, null=True)
    date_finished = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.group, self.respondent or "General")

    class Meta:
        verbose_name = "Respuesta de grupo"
        verbose_name_plural = "Respuestas de grupos"


class PrioritizedComponent(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    group_answer = models.ForeignKey(
        GroupAnswer, on_delete=models.CASCADE, related_name="prioritized")
    # group = models.ForeignKey(
    #     Group, on_delete=models.CASCADE, related_name="prioritized")
    is_prioritized = models.BooleanField(blank=True, null=True)
    is_low_priority = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.component, self.group_answer)

    class Meta:
        verbose_name = "Priorización de componente"
        verbose_name_plural = "Priorizaciones de componentes"


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
