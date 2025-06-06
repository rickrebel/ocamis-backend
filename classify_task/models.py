from django.db import models
from django.contrib.auth.models import User


class StatusTask(models.Model):

    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    # description = models.CharField(
    #     blank=True, null=True, max_length=255, verbose_name="Descripción")
    order = models.IntegerField(default=5)
    icon = models.CharField(max_length=30, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    macro_status = models.CharField(
        max_length=30, blank=True, null=True, default="in_progress")

    def __str__(self):
        return self.public_name or self.name

    class Meta:
        ordering = ['order']
        verbose_name = "Status de tarea"
        verbose_name_plural = "3. Status de tareas"


class TaskFunction(models.Model):
    MODEL_CHOICES = (
        ("petition", "Solicitud (Petición)"),
        ("file_control", "Grupo de Control"),
        ("data_file", "DataFile (archivo de datos)"),
        ("reply_file", "ReplyFile (.zip)"),
        ("sheet_file", "Hoja (sheet)"),
        # ("3entity_week", "Semana Proveedor"),
        ("week_record", "Semana Proveedor"),
        # ("3entity_month", "Mes Proveedor"),
        ("month_record", "Mes Proveedor"),
        ("provider", "Proveedor"),
        ("cluster", "Cluster"),
        ("mat_view", "Materialized View"),
    )

    name = models.CharField(max_length=100, primary_key=True)
    lambda_function = models.CharField(max_length=100, blank=True, null=True)

    model_name = models.CharField(
        max_length=100, choices=MODEL_CHOICES, blank=True, null=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    is_active = models.BooleanField(default=False, verbose_name="active")
    is_from_aws = models.BooleanField(default=False, verbose_name="AWS")
    is_queueable = models.BooleanField(default=False, verbose_name="queue")
    ebs_percent = models.IntegerField(default=0, verbose_name="% EBS")
    queue_size = models.IntegerField(default=1, verbose_name="queue size")
    group_queue = models.CharField(
        max_length=100, choices=MODEL_CHOICES, blank=True, null=True,
        verbose_name="agrupables")
    simultaneous_groups = models.IntegerField(
        default=1, verbose_name="Grupos simultáneos")

    def __str__(self):
        active_mark = "✅" if self.is_active else "❌"
        # aws_mark = "🌐" if self.is_from_aws else ""
        if self.model_name:
            initials_model_name = self.model_name.split("_")
            mini_model_name = "".join([x[0] for x in initials_model_name])
        else:
            mini_model_name = ""
        if self.lambda_function and self.lambda_function != self.name:
            mini_model_name = f"{self.lambda_function}-{mini_model_name}"
        aws_mark = "↕️ " if self.is_from_aws else ""
        return f"{aws_mark}{self.name} ({mini_model_name}) {active_mark}"

    class Meta:
        verbose_name = "Función (tarea)"
        ordering = ['-is_active', 'model_name', '-is_from_aws', 'name']
        verbose_name_plural = "2. Funciones (tareas)"


STAGE_GROUP_CHOICES = (
    ("transformation", "Transformación"),
    ("months", "Meses"),
    ("provider", "Proveedor"),
    ("provider-petition", "Proveedor (Solicitud)"),
    ("provider-control", "Proveedor (Grupos de control)"),
    ("provider-month", "Proveedor (Meses)"),
    ("cluster", "Cluster"),
)


class Stage(models.Model):
    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120)
    stage_group = models.CharField(
        max_length=30, choices=STAGE_GROUP_CHOICES, blank=True, null=True)
    action_text = models.CharField(
        max_length=120, blank=True, null=True)
    action_verb = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=5)
    icon = models.CharField(max_length=30, blank=True, null=True)
    main_function = models.ForeignKey(
        TaskFunction, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="Función principal", related_name="stages")
    next_stage = models.OneToOneField(
        "Stage", blank=True, null=True, on_delete=models.CASCADE,
        related_name="previous_stage")
    function_after = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Función llegando de Lambda")
    finished_function = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Función al terminar hijos")
    available_next_stages = models.ManyToManyField(
        "Stage", blank=True, related_name="previous_stages")
    re_process_stages = models.ManyToManyField(
        "Stage", blank=True, related_name="re_processing",
        verbose_name="Etapas a re-procesar")
    can_self_revert = models.BooleanField(default=False)
    field_last_edit = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Campo de última edición")

    def save(self, *args, **kwargs):
        from task.models import Step
        from geo.models import Provider
        # RICK 24: Revisar qué onda con esto, está raro
        if self.stage_group == "provider":
            for provider in Provider.objects.all():
                Step.objects.get_or_create(
                    stage=self, status_operative_id="initial_register")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} \n({self.public_name})"

    class Meta:
        ordering = ['order']
        verbose_name = "Etapa"
        verbose_name_plural = "4. Etapas"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    has_tasks = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to="profile_images", blank=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "1. Perfiles de usuario"
