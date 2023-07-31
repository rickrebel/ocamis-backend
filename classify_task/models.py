from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import User


class StatusTask(models.Model):

    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
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
        db_table = 'classify_task_statustask'


class TaskFunction(models.Model):
    MODEL_CHOICES = (
        ("petition", "Solicitud (Petición)"),
        ("file_control", "Grupo de Control"),
        ("data_file", "DataFile (archivo de datos)"),
        ("reply_file", "ReplyFile (.zip)"),
        ("sheet_file", "Pestaña"),
        ("entity_week", "Semana Proveedor"),
        ("entity_month", "Mes Proveedor"),
        ("entity", "Proveedor"),
    )

    name = models.CharField(max_length=100, primary_key=True)
    model_name = models.CharField(
        max_length=100, choices=MODEL_CHOICES, blank=True, null=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    is_active = models.BooleanField(default=False, verbose_name="active")
    is_from_aws = models.BooleanField(default=False, verbose_name="AWS")
    is_queueable = models.BooleanField(default=False, verbose_name="queue")
    queue_size = models.IntegerField(default=1, verbose_name="queue size")
    group_queue = models.CharField(
        max_length=100, choices=MODEL_CHOICES, blank=True, null=True,
        verbose_name="agrupables")
    simultaneous_groups = models.IntegerField(
        default=1, verbose_name="Grupos simultáneos")

    def __str__(self):
        active_mark = "✅" if self.is_active else "❌"
        aws_mark = "🌐" if self.is_from_aws else ""
        return f"{active_mark} {self.name} ({self.model_name}){aws_mark}"

    class Meta:
        verbose_name = "Función (tarea)"
        ordering = ['-is_active', 'model_name', '-is_from_aws', 'name']
        verbose_name_plural = "2. Funciones (tareas)"


class Stage(models.Model):
    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120)
    action_text = models.CharField(
        max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=5)
    icon = models.CharField(max_length=30, blank=True, null=True)
    # next_function = models.ForeignKey(
    #     "TaskFunction", blank=True, null=True, on_delete=models.CASCADE,
    #     related_name="next_functions")
    main_function = models.ForeignKey(
        "TaskFunction", blank=True, null=True, on_delete=models.CASCADE,
        verbose_name="Función principal", related_name="stages")
    #function_from_aws = models.
    next_stage = models.OneToOneField(
        "Stage", blank=True, null=True, on_delete=models.CASCADE,
        related_name="previous_stage")
    available_next_stages = models.ManyToManyField(
        "Stage", blank=True, related_name="previous_stages")
    re_process_stages = models.ManyToManyField(
        "Stage", blank=True, related_name="re_processing",
        verbose_name="Etapas a re-procesar")

    def __str__(self):
        return f"{self.order}. {self.public_name or self.name}"

    class Meta:
        ordering = ['order']
        verbose_name = "Etapa"
        verbose_name_plural = "4. Etapas"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    has_tasks = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to="profile_images", blank=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "1. Perfiles de usuario"
