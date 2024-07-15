from django.db import models
from django.db.models import JSONField
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from inai.models import Petition, MonthRecord, WeekRecord
from respond.models import ReplyFile, DataFile, SheetFile, TableFile
from geo.models import Provider
from data_param.models import FileControl, Collection
from classify_task.models import StatusTask, TaskFunction, Stage
from category.models import StatusControl
from rds.models import Cluster, MatView, Operation


class TaskManager(models.Manager):

    def in_queue(self, ebs=False, **kwargs):
        query_task = self\
            .filter(status_task__name="queued", **kwargs)\
            .order_by("id")
        if ebs:
            query_task = query_task.filter(task_function__ebs_percent__gt=0)
        else:
            query_task = query_task.filter(task_function__ebs_percent=0)
        return query_task


class AsyncTask(models.Model):

    request_id = models.CharField(max_length=100, blank=True, null=True)
    parent_task = models.ForeignKey(
        "self", related_name="child_tasks",
        blank=True, null=True, on_delete=models.CASCADE)

    provider = models.ForeignKey(
        Provider, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    week_record = models.ForeignKey(
        WeekRecord, related_name="async_tasks",
        on_delete=models.CASCADE, blank=True, null=True)
    month_record = models.ForeignKey(
        MonthRecord, related_name="async_tasks",
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
    # cluster = models.ForeignKey(
    #     Cluster, related_name="async_tasks",
    #     on_delete=models.CASCADE, blank=True, null=True)
    # operation = models.ForeignKey(
    #     Operation, related_name="async_tasks",
    #     on_delete=models.CASCADE, blank=True, null=True)
    # mat_view = models.ForeignKey(
    #     MatView, related_name="async_tasks",
    #     on_delete=models.CASCADE, blank=True, null=True)

    status_task = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE,
        default="created", verbose_name="Estado de la tarea")
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
        User, on_delete=models.CASCADE, blank=True, null=True,
        related_name="async_tasks")
    result = JSONField(blank=True, null=True)
    errors = JSONField(blank=True, null=True)
    is_current = models.BooleanField(default=True, verbose_name="last")
    traceback = models.TextField(blank=True, null=True)

    date_start = models.DateTimeField(blank=True, null=True)
    date_sent = models.DateTimeField(blank=True, null=True)
    date_arrive = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    # new_task: list = []
    # models: list = []

    # def __init__(self, *args, **kwargs):
    #     self.new_task = kwargs.pop("new_task", None)
    #     super().__init__(*args, **kwargs)
    #     # self.new_task = []

    # def save(self, *args, **kwargs):
    #     post_models = kwargs.pop("models", [])
    #     for model in post_models:
    #         model_name = camel_to_snake(model.__class__.__name__)
    #         setattr(self, model_name, model)
    #         return model_name
    #
    #     super().save(*args, **kwargs)

    objects = TaskManager()

    def save_status(self, status_id=None):
        from datetime import datetime
        is_changed = self.status_task_id != status_id
        if is_changed:
            if status_id:
                self.status_task_id = status_id
            else:
                self.status_task_id = self.status_task_id
            is_completed = StatusTask.objects.filter(
                name=self.status_task_id, is_completed=True).exists()
            if is_completed and not self.date_end:
                self.date_end = datetime.now()
            # if self.status_task_id == "finished":
            #     self.is_current = False
            #     self.save()
        self.save()
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
        # return "%s -- %s" % (self.task_function.name, self.status_task)
        function_name = self.task_function.name if self.task_function else "??"
        return "%s -- %s" % (function_name, self.status_task)

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


class CutOff(models.Model):
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE,
        verbose_name="Entidad", related_name="cut_offs")
    last_month_record = models.ForeignKey(
        MonthRecord, on_delete=models.CASCADE,
        verbose_name="Mes de corte", blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.provider, self.last_month_record)

    class Meta:
        verbose_name = "Corte de pasos"
        verbose_name_plural = "Cortes de pasos"


class Step(models.Model):
    cut_off = models.ForeignKey(
        CutOff, on_delete=models.CASCADE,
        verbose_name="Corte", related_name="steps")
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        verbose_name="Etapa")
    status_operative = models.ForeignKey(
        StatusControl, on_delete=models.CASCADE,
        verbose_name="Status", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Último usuario en modificar",
        blank=True, null=True)
    last_update = models.DateTimeField(
        verbose_name="Última modificación", blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.cut_off, self.stage)

    class Meta:
        verbose_name = "Paso"
        verbose_name_plural = "Pasos"
        ordering = ["-stage__order"]


class ClickHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Usuario", related_name="clicks")
    month_record = models.ForeignKey(
        MonthRecord, on_delete=models.CASCADE,
        verbose_name="Mes", blank=True, null=True)
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE,
        verbose_name="Petición", blank=True, null=True)
    file_control = models.ForeignKey(
        FileControl, on_delete=models.CASCADE,
        verbose_name="Control de archivos", blank=True, null=True)
    date = models.DateTimeField(
        verbose_name="Fecha", blank=True, null=True, auto_now_add=True)

    def __str__(self):
        return "%s - %s" % (self.user, self.date)

    class Meta:
        verbose_name = "Historial"
        verbose_name_plural = "Historial"
        ordering = ["-date"]


OFFLINE_TYPES = (
    ('weekly_meeting', 'Reunión semanal'),
    ('meeting', 'Reunión'),
    ('training', 'Capacitación'),
    ('pnt', 'Solicitudes INAI'),
    ('other', 'Otro'),
)


class OfflineTask(models.Model):
    users = models.ManyToManyField(User, related_name="offline_tasks")
    date_start = models.DateTimeField(verbose_name="Inicio")
    date_end = models.DateTimeField(verbose_name="Fin")
    activity_type = models.CharField(
        max_length=100, choices=OFFLINE_TYPES, verbose_name="Tipo")
    name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Actividad")
    user_added = models.ForeignKey(
        User, blank=True, null=True,
        on_delete=models.DO_NOTHING, related_name="offline_tasks_added")

    def __str__(self):
        return "%s - %s" % (self.date_start, self.date_end)

    class Meta:
        verbose_name = "Tarea offline"
        verbose_name_plural = "Tareas offline"
        ordering = ["-date_start"]


class FilePath(models.Model):
    reply_file = models.ForeignKey(
        ReplyFile, on_delete=models.CASCADE, blank=True, null=True,
        related_name="file_paths")
    data_file = models.ForeignKey(
        DataFile, on_delete=models.CASCADE, blank=True, null=True)
    sheet_file = models.ForeignKey(
        SheetFile, on_delete=models.CASCADE, blank=True, null=True)
    table_file = models.ForeignKey(
        TableFile, on_delete=models.CASCADE, blank=True, null=True)
    path_to_file = models.CharField(
        max_length=400, verbose_name="Ruta al archivo deseable")
    path_in_bucket = models.CharField(
        max_length=400, verbose_name="Ruta al archivo actual")
    size = models.IntegerField(blank=True, null=True)
    is_correct_path = models.BooleanField(blank=True, null=True)
    # status = models.CharField(
    #     max_length=100, blank=True, null=True)

    def __str__(self):
        return self.path_to_file

    class Meta:
        verbose_name = "Ruta de archivo"
        verbose_name_plural = "Rutas de archivo"
        ordering = ["-id"]

