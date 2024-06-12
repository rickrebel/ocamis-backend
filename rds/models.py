from django.db import models
from django.db.models import JSONField
from classify_task.models import StatusTask, TaskFunction, Stage
from data_param.models import Collection
from geo.models import Provider


class Platform(models.Model):
    version = models.CharField(max_length=10)
    has_constrains = models.BooleanField(default=True)
    create_constraints = JSONField(blank=True, null=True)
    delete_constraints = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Plataforma"
        verbose_name_plural = "Plataformas"
        db_table = "rds_platform"

    def __str__(self):
        return self.version


# CLUSTERS = (
#     ('iss', 'Instituciones de Seguridad Social'),
#     ('stable', 'Instituciones con información estable'),
#     ('other', 'Otras instituciones'),
# )

class Cluster(models.Model):
    name = models.CharField(max_length=80, primary_key=True)
    public_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Nombre público")
    providers = models.ManyToManyField(
        Provider, related_name="clusters", blank=True)

    def __str__(self):
        return f"{self.name} ({self.public_name})"

    def display_providers(self):
        return ', '.join([provider.acronym for provider in self.providers.all()])

    class Meta:
        verbose_name = "Cluster"
        verbose_name_plural = "Clusters"


class ClusterYear(models.Model):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    year = models.IntegerField()
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='init_cluster', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')

    def __str__(self):
        return f"{self.cluster} - {self.year}"

    class Meta:
        verbose_name = "Cluster por año"
        verbose_name_plural = "Clusters por año"


class MatView(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    public_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Nombre público")
    description = models.TextField(blank=True, null=True)
    script = models.TextField()
    is_active = models.BooleanField(default=True)
    stage_belongs = models.ForeignKey(
        Stage, on_delete=models.CASCADE, default='init_mat_view',
        verbose_name="Etapa de creación", related_name="mat_views")
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, default='init_mat_view',
        verbose_name="Etapa actual", related_name="mvs")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')

    def __str__(self):
        return f"{self.name} ({self.public_name})"

    class Meta:
        verbose_name = "Materialized View"
        verbose_name_plural = "Materialized Views"


OPERATION_CHOICES = (
    ("clean", "Limpiar de constrains"),
    ("constraint", "constraint"),
    ("index", "index"),
    ("materialized", "materialized view"),
    ("union", "union"),
    ("index_union", "index of consolidated materialized view"),
)


class Operation(models.Model):
    operation_type = models.CharField(
        max_length=20, choices=OPERATION_CHOICES)
    order = models.IntegerField(default=40)
    low_priority = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    script = models.TextField()
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, blank=True, null=True)
    mat_view = models.ForeignKey(
        MatView, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.script

    class Meta:
        verbose_name = "Operación"
        verbose_name_plural = "Operaciones"
        # ordering = ["priority"]


# class OperationCluster(models.Model):
#     operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
#     cluster_year = models.ForeignKey(ClusterYear, on_delete=models.CASCADE)
#     status = models.ForeignKey(
#         StatusTask, on_delete=models.CASCADE, default='finished')
#
#     class Meta:
#         verbose_name = "Operación Cluster"
#         verbose_name_plural = "Operaciones Cluster"
#
#     def __str__(self):
#         return self.operation.script
#
