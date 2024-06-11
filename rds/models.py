from django.db import models
from django.db.models import JSONField


# from django.db.models import JSONField
# from classify_task.models import StatusTask, TaskFunction, Stage


# class Cluster(models.Model):
#     name = models.CharField(max_length=80, primary_key=True)
#     public_name = models.CharField(
#         max_length=255, blank=True, null=True,
#         verbose_name="Nombre público")
#     # providers = models.ManyToManyField(
#     #     Provider, related_name="clusters", blank=True)
#
#     def __str__(self):
#         return f"{self.name} ({self.public_name})"
#
#     class Meta:
#         verbose_name = "Cluster"
#         verbose_name_plural = "Clusters"
#         db_table = "rds_cluster"
#
#
# class ClusterYear(models.Model):
#     cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
#     year = models.IntegerField()
#     stage = models.ForeignKey(
#         Stage, on_delete=models.CASCADE,
#         default='init_cluster', verbose_name="Etapa actual")
#     status = models.ForeignKey(
#         StatusTask, on_delete=models.CASCADE, default='finished')
#
#     def __str__(self):
#         return f"{self.cluster} - {self.year}"
#
#     class Meta:
#         verbose_name = "Cluster por año"
#         verbose_name_plural = "Clusters por año"
#         db_table = "rds_clusteryear"
#
#
# OPERATION_CHOICES = (
#     ("clean", "Limpiar de constrains"),
#     ("constraint", "constraint"),
#     ("index", "index"),
#     ("materialized", "materialized view"),
#     ("union", "union"),
#     ("index_union", "index of materialized view"),
# )
#
#
# class Operation(models.Model):
#     platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
#     operation_type = models.CharField(
#         max_length=100, choices=OPERATION_CHOICES)
#     priority = models.IntegerField()
#     script = models.TextField()
#
#     def __str__(self):
#         return self.script
#
#     class Meta:
#         verbose_name = "Operación"
#         verbose_name_plural = "Operaciones"
#         ordering = ["priority"]
#         db_table = "rds_operation"
#
#
# class OperationCluster(models.Model):
#     operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
#     cluster_year = models.ForeignKey(ClusterYear, on_delete=models.CASCADE)
#     status = models.ForeignKey(
#         StatusTask, on_delete=models.CASCADE, default='finished')
#
#     class Meta:
#         verbose_name = "Operación Cluster"
#         verbose_name_plural = "Operaciones Cluster"
#         db_table = "rds_operationcluster"
#
#     def __str__(self):
#         return self.operation.script
class Platform(models.Model):
    version = models.CharField(max_length=10)
    has_constrains = models.BooleanField(default=True)
    # collection = models.ForeignKey(
    #     Collection, on_delete=models.CASCADE, blank=True, null=True)
    create_constraints = JSONField(blank=True, null=True)
    delete_constraints = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Plataforma"
        verbose_name_plural = "Plataformas"
        db_table = "rds_platform"

    def __str__(self):
        return self.version
