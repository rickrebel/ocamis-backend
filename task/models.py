from django.db import models
from django.db.models import JSONField
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from django.contrib.auth.models import User
from inai.models import (
    Petition, DataFile, ReplyFile, SheetFile, EntityWeek, EntityMonth,)
from geo.models import Entity
from data_param.models import FileControl
from classify_task.models import StatusTask, TaskFunction


class AsyncTask(models.Model):

    request_id = models.CharField(max_length=100, blank=True, null=True)
    parent_task = models.ForeignKey(
        "self", related_name="child_tasks",
        blank=True, null=True, on_delete=models.CASCADE)
    entity = models.ForeignKey(
        Entity, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    entity_week = models.ForeignKey(
        EntityWeek, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    entity_month = models.ForeignKey(
        EntityMonth, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    petition = models.ForeignKey(
        Petition, blank=True, null=True,
        related_name="async_tasks",
        on_delete=models.CASCADE)
    reply_file = models.ForeignKey(
        ReplyFile, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    data_file = models.ForeignKey(
        DataFile, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    sheet_file = models.ForeignKey(
        SheetFile, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    status_task = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name="Estado de la tarea")
    function_name = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Nombre de la función")
    task_function = models.ForeignKey(
        TaskFunction, blank=True, null=True, on_delete=models.CASCADE,
        related_name="functions")
    is_massive = models.BooleanField(default=False, verbose_name="many")
    subgroup = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Subtipo de la función")
    function_after = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Función a ejecutar después")
    finished_function = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Función a ejecutar si es exitosa")
    original_request = JSONField(
        blank=True, null=True, verbose_name="Request original")
    params_after = JSONField(
        blank=True, null=True, verbose_name="Parámetros de la función after")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    result = JSONField(blank=True, null=True)
    errors = JSONField(blank=True, null=True)
    is_current = models.BooleanField(
        default=True, verbose_name="last")
    traceback = models.TextField(blank=True, null=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_sent = models.DateTimeField(blank=True, null=True)
    date_arrive = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    def save_status(self, status_id=None):
        from datetime import datetime
        if status_id:
            self.status_task_id = status_id
        else:
            self.status_task_id = self.status_task_id
        is_completed = StatusTask.objects.filter(
            name=self.status_task_id, is_completed=True).exists()
        if is_completed and not self.date_end:
            self.date_end = datetime.now()
        self.save()
        # if self.status_task_id == "finished":
        #     self.is_current = False
        #     self.save()
        return self

    @property
    def can_repeat(self):
        from datetime import datetime, timedelta
        if self.status_task.is_completed:
            return True
        x_minutes = 15
        quick_status = ['success', 'pending', 'created']
        if self.status_task.name in quick_status:
            x_minutes = 2
        more_than_x_minutes = (
            datetime.now() - self.date_start) > timedelta(minutes=x_minutes)
        return more_than_x_minutes

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
    from task.api.serializers import (
        AsyncTaskFullSerializer, AsyncTaskSerializer)
    channel_layer = get_channel_layer()
    serializer = AsyncTaskFullSerializer \
        if instance.is_current else AsyncTaskSerializer
    # serializer = AsyncTaskSerializer
    # print("channel_layer", channel_layer)
    async_to_sync(channel_layer.group_send)(
        "dashboard", {
            "type": "send_task_info",
            "result": {
                "model": sender.__name__,
                "created": created,
                "task_data": serializer(instance).data,
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


class Platform(models.Model):
    version = models.CharField(max_length=10)
    has_constrains = models.BooleanField(default=True)
    # has_mini_constrains = models.BooleanField(default=False)
    create_constraints = JSONField(blank=True, null=True)
    delete_constraints = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = u"Plataforma"
        verbose_name_plural = "Plataformas"
        ordering = ["-version"]

    def __str__(self):
        return self.version
