from django.db import models
from geo.models import Agency, Provider
from rds.models import Cluster
from classify_task.models import Stage, StatusTask


class MonthRecord(models.Model):
    agency = models.ForeignKey(
        Agency,
        verbose_name="Sujeto Obligado",
        related_name="months",
        on_delete=models.CASCADE, blank=True, null=True)
    provider = models.ForeignKey(
        Provider,
        related_name="month_records",
        verbose_name="Proveedor de servicios de salud",
        on_delete=models.CASCADE, blank=True, null=True)
    cluster = models.ForeignKey(
        Cluster, on_delete=models.CASCADE,
        blank=True, null=True, related_name="month_records")
    year_month = models.CharField(max_length=10)
    year = models.SmallIntegerField(blank=True, null=True)
    month = models.SmallIntegerField(blank=True, null=True)
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE,
        default='init_month', verbose_name="Etapa actual")
    status = models.ForeignKey(
        StatusTask, on_delete=models.CASCADE, default='finished')
    error_process = models.JSONField(blank=True, null=True)

    drugs_count = models.IntegerField(default=0)
    drugs_in_pre_insertion = models.IntegerField(default=0)
    rx_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    shared_count = models.IntegerField(default=0)
    last_transformation = models.DateTimeField(blank=True, null=True)
    last_crossing = models.DateTimeField(blank=True, null=True)
    last_behavior = models.DateTimeField(blank=True, null=True)
    last_merge = models.DateTimeField(blank=True, null=True)
    last_pre_insertion = models.DateTimeField(blank=True, null=True)
    last_validate = models.DateTimeField(blank=True, null=True)
    last_indexing = models.DateTimeField(blank=True, null=True)
    last_insertion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s -- %s" % (self.provider.acronym, self.year_month)

    def end_stage(self, stage_id, main_task):
        child_task_errors = main_task.child_tasks.filter(
            status_task__macro_status="with_errors")
        all_errors = []
        for child_task_error in child_task_errors:
            current_errors = child_task_error.errors
            if not current_errors:
                g_children = child_task_error.child_tasks.filter(
                    status_task__macro_status="with_errors")
                for g_child in g_children:
                    if g_child:
                        try:
                            current_errors += g_child.errors or []
                        except Exception as e:
                            message = (
                                f"Error en MonthRecord.end_stage: {e}"
                                f"g_child.errors: {g_child.errors}"
                                f"current_errors: {current_errors}")
                            raise Exception(message)
            all_errors += current_errors or []
        self.stage_id = stage_id
        if child_task_errors.exists():
            self.status_id = "with_errors"
            self.error_process = all_errors
        else:
            self.status_id = "finished"
            self.error_process = None
        self.save()
        return all_errors

    def save_stage(self, stage_id: str, errors=None):
        self.stage_id = stage_id
        if errors:
            self.status_id = "with_errors"
            self.error_process = errors
        else:
            self.status_id = "finished"
            self.error_process = []
        self.save()

    def save_error_process(self, errors):
        self.error_process = errors
        self.status_id = "with_errors"
        self.save()

    @property
    def human_name(self):
        months = [
            "ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic"]
        year, month = self.year_month.split("-")
        month_name = months[int(month)-1]
        return "%s/%s" % (month_name, year)

    @property
    def temp_table(self):
        year_month = self.year_month.replace("-", "")
        return f"{self.provider_id}_{year_month}"

    @property
    def base_table(self):
        # cluster = self.provider.clusters.first()
        # year = self.year_month.split("-")[0]
        return f"{self.cluster.name}"

    class Meta:
        get_latest_by = "year_month"
        db_table = "inai_entitymonth"
        ordering = ["year_month"]
        verbose_name = "8. Mes-proveedor"
        verbose_name_plural = "8. Meses-proveedores"
