from django.db import models
from django.db.models import JSONField
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from django.contrib.auth.models import User
from inai.models import Petition, DataFile, ReplyFile
from data_param.models import FileControl


class AsyncTask(models.Model):

    request_id = models.CharField(max_length=100, blank=True, null=True)
    parent_task = models.ForeignKey(
        "self", related_name="child_tasks",
        blank=True, null=True, on_delete=models.CASCADE)
    file_control = models.ForeignKey(
        FileControl, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    # file_control = models.IntegerField(blank=True, null=True)
    petition = models.ForeignKey(
        Petition, blank=True, null=True,
        related_name="async_tasks",
        on_delete=models.CASCADE)
    data_file = models.ForeignKey(
        DataFile, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    process_file = models.ForeignKey(
        ReplyFile, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    status_task = models.ForeignKey(
        "StatusTask", on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Estado de la tarea")
    function_name = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Nombre de la función")
    task_function = models.ForeignKey(
        "TaskFunction", blank=True, null=True, on_delete=models.CASCADE,
        related_name="functions")
    subgroup = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Subtipo de la función")
    function_after = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Función a ejecutar después")
    original_request = JSONField(
        blank=True, null=True, verbose_name="Request original")
    params_after = JSONField(
        blank=True, null=True, verbose_name="Parámetros de la función after")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    result = JSONField(blank=True, null=True)
    # error = models.TextField(blank=True, null=True)
    errors = JSONField(blank=True, null=True)
    is_current = models.BooleanField(
        default=True, verbose_name="last")
    traceback = models.TextField(blank=True, null=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_arrive = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    def save_status(self, status_id=None):
        if status_id:
            self.status_task_id = status_id
        else:
            self.status_task_id = self.status_task_id
        self.save()
        return self

    def __str__(self):
        return "%s -- %s" % (self.task_function.name, self.status_task)

    def display_name(self):
        return "%s -- %s" % (self.task_function.name, self.status_task)

    class Meta:
        ordering = ["-date_start"]
        verbose_name = "Tarea solicitada"
        verbose_name_plural = "1. Tareas solicitadas"


@receiver(post_save, sender=AsyncTask)
def async_task_post_save(sender, instance, created, **kwargs):
    # print("kwargs", kwargs)
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from task.api.serializers import AsyncTaskFullSerializer
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard", {
            "type": "send_task_info",
            "result": {
                "model": sender.__name__,
                "created": created,
                "task_data": AsyncTaskFullSerializer(instance).data,
            }
        },
    )


@receiver(post_delete, sender=AsyncTask)
def async_task_post_delete(sender, instance, **kwargs):
    # print("kwargs", kwargs)
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard", {
            "type": "send_task_info",
            "result": {
                "model": sender.__name__,
                "deleted": True,
                "task_id": instance.id,
            }
        },
    )


class StatusTask(models.Model):

    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=5)
    icon = models.CharField(max_length=30, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    is_completed = models.BooleanField(default=False)

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
        ("process_file", "ReplyFile (.zip)"),
    )

    name = models.CharField(max_length=100, primary_key=True)
    model_name = models.CharField(
        max_length=100, choices=MODEL_CHOICES, blank=True, null=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=30, blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Función (tarea)"
        verbose_name_plural = "2. Funciones (tareas)"

