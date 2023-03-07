from django.db import models


# class Stage(models.Model):
#     name = models.CharField(max_length=80, primary_key=True)
#     public_name = models.CharField(max_length=120)
#     description = models.TextField(blank=True, null=True)
#     order = models.IntegerField(default=5)
#     icon = models.CharField(max_length=30, blank=True, null=True)
#     color = models.CharField(max_length=30, blank=True, null=True)
#     next_function = models.ForeignKey(
#         "TaskFunction", blank=True, null=True, on_delete=models.CASCADE,
#         related_name="next_functions")
#     next_text = models.TextField(
#         blank=True, null=True, verbose_name="Texto para continuar")
#     massive_next_text = models.TextField(
#         blank=True, null=True, verbose_name="Texto - continuar masivamente")
#     retry_function = models.ForeignKey(
#         "TaskFunction", blank=True, null=True, on_delete=models.CASCADE,
#         related_name="try_functions")
#     retry_text = models.TextField(
#         blank=True, null=True, verbose_name="Texto para reintentar")
#     massive_retry_text = models.TextField(
#         blank=True, null=True, verbose_name="Texto - reintentar masivamente")
#
#     def __str__(self):
#         return self.public_name or self.name
#
#     class Meta:
#         ordering = ['order']
#         verbose_name = "Etapa"
#         verbose_name_plural = "4. Etapas"
#
