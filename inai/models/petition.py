from django.db import models
from geo.models import Agency, Provider
from .month_record import MonthRecord
from category.models import StatusControl, InvalidReason
from data_param.models import DataGroup


class RequestTemplate(models.Model):
    version = models.IntegerField(blank=True, null=True)
    version_name = models.CharField(max_length=100, blank=True, null=True)
    text = models.TextField()
    description = models.TextField(blank=True, null=True)
    provider = models.ForeignKey(
        Provider, related_name="request_templates",
        verbose_name="Proveedor",
        on_delete=models.CASCADE, null=True, blank=True)
    data_groups = models.ManyToManyField(
        DataGroup, blank=True, verbose_name="Grupos de datos")

    def __str__(self):
        return self.version_name or str(self.version)

    def save(self, *args, **kwargs):
        if not self.version_name:
            self.version_name = f"Versión {self.version}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Plantilla de solicitud"
        verbose_name_plural = "CAT. Plantillas de solicitud"
        ordering = ["-id"]


class Petition(models.Model):

    folio_petition = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Folio de la solicitud")
    id_inai_open_data = models.IntegerField(
        verbose_name="Id en el sistema de INAI",
        blank=True, null=True)
    agency = models.ForeignKey(
        Agency, related_name="petitions",
        on_delete=models.CASCADE)
    real_provider = models.ForeignKey(
        Provider, related_name="real_petitions",
        on_delete=models.CASCADE, null=True, blank=True)
    month_records = models.ManyToManyField(
        MonthRecord, blank=True, verbose_name="Meses de la solicitud")
    description_petition = models.TextField(
        verbose_name="descripción enviada",
        blank=True, null=True)
    description_response = models.TextField(
        verbose_name="Respuesta texto",
        blank=True, null=True)
    send_petition = models.DateField(
        verbose_name="Fecha de envío o recepción",
        blank=True, null=True)
    response_limit = models.DateField(
        verbose_name="Fecha límite de respuesta",
        blank=True, null=True)
    send_response = models.DateField(
        verbose_name="Fecha de última respuesta",
        blank=True, null=True)
    complain_send_limit = models.DateField(
        verbose_name="Fecha límite de envío de queja",
        blank=True, null=True)
    status_petition = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_petition",
        verbose_name="Status de la petición",
        on_delete=models.CASCADE)
    status_data = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_data",
        verbose_name="Status de los datos entregados",
        on_delete=models.CASCADE)
    status_priority = models.ForeignKey(
        StatusControl, null=True, blank=True,
        related_name="petitions_priority",
        verbose_name="Status de prioridad",
        on_delete=models.CASCADE)
    invalid_reason = models.ForeignKey(
        InvalidReason, null=True, blank=True,
        verbose_name="Razón de invalidez",
        on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    template_text = models.TextField(
        blank=True, null=True, verbose_name="Texto para la plantilla")
    request_template = models.ForeignKey(
        RequestTemplate, related_name="petitions",
        on_delete=models.CASCADE, null=True, blank=True)
    template_variables = models.JSONField(
        blank=True, null=True, verbose_name="Variables de la plantilla")

    # Need to move to own model
    months_verified = models.BooleanField(
        verbose_name="Meses verificados", default=False)
    reasons_verified = models.BooleanField(
        verbose_name="Razones verificadas", default=False)
    reply_files_verified = models.BooleanField(
        verbose_name="Archivos de respuesta verificados", default=False)

    # Complain data, needs to be moved to another model
    # info_queja_inai = JSONField(
    #     verbose_name="Datos de queja",
    #     help_text="Información de la queja en INAI Search",
    #     blank=True, null=True)

    def delete(self, *args, **kwargs):
        from respond.models import LapSheet
        some_lap_inserted = LapSheet.objects.filter(
            sheet_file__data_file__petition_file_control__petition=self,
            inserted=True).exists()
        if some_lap_inserted:
            raise Exception("No se puede eliminar un archivo con datos insertados")
        super().delete(*args, **kwargs)

    def first_year_month(self):
        if self.month_records.exists():
            return self.month_records.earliest().year_month
        return None

    def last_year_month(self):
        if self.month_records.exists():
            return self.month_records.latest().year_month
        return None

    @property
    def orphan_pet_control(self):
        from data_param.models import FileControl
        from inai.models import PetitionFileControl
        orphan = self.file_controls\
            .filter(file_control__data_group_id="orphan")\
            .first()
        if not orphan:
            name_control = "Archivos por agrupar. Solicitud %s" % (
                self.folio_petition)
            file_control, created = FileControl.objects.get_or_create(
                name=name_control,
                data_group_id="orphan",
                final_data=False,
                agency=self.agency,
            )
            orphan, _ = PetitionFileControl.objects.get_or_create(
                petition=self, file_control=file_control)
        return orphan

    def months(self):
        # html_list = ''
        start = self.month_records.earliest().year_month
        end = self.month_records.latest().year_month
        return " ".join(list({start, end}))
    months.short_description = "Meses"

    def months_in_description(self):
        from django.utils.html import format_html
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        curr_months = []
        if self.description_petition:
            description = self.description_petition.lower()
            for month in months:
                if month in description:
                    curr_months.append(month)
            html_list = ''
            for month in list(curr_months):
                html_list = html_list + ('<span>%s</span><br>' % month)
            return format_html(html_list)
        else:
            return "Sin descripción"
    months_in_description.short_description = "Meses escritos"

    def get_orphan_pfc(self, forced_create=False):
        from data_param.models import FileControl
        from inai.models import PetitionFileControl

        try:
            return self.file_controls.get(file_control__data_group_id='orphan')
        except PetitionFileControl.DoesNotExist:
            if not forced_create:
                return None

        name_control = f"Archivos por agrupar. Solicitud {self.folio_petition}"

        file_control, _ = FileControl.objects.get_or_create(
            name=name_control,
            data_group_id='orphan',
            final_data=False,
            agency=self.agency,
        )
        if self.real_provider:
            file_control.real_provider = self.real_provider
            file_control.save()
        orphan_pfc, _ = PetitionFileControl.objects \
            .get_or_create(file_control=file_control, petition=self)
        return orphan_pfc

    def delete_orphan_pfc(self):
        orphan_pfc = self.get_orphan_pfc()
        if orphan_pfc:
            orphan_pfc.delete()

    def __str__(self):
        return f"solicitud {self.folio_petition or 'draft'} - {self.agency}"
        # return "%s -- %s" % (self.agency, self.folio_petition or self.id)

    class Meta:
        verbose_name = "Solicitud - Petición"
        verbose_name_plural = "1. Solicitudes (Peticiones)"
