from django.db import models

class NecDelegacionImss(models.Model):
    cve_delegacion_imss = models.TextField(primary_key=True)
    nom_delegacion_imss = models.TextField()

class NecUnidadMedicaClues(models.Model):
    cve_unidad_clues = models.TextField(primary_key=True)
    cve_clues = models.TextField()
    des_tipologia_unidad = models.TextField()

class NetUnidadMedica(models.Model):
    cve_delegacion = models.ForeignKey(
        NecDelegacionImss, on_delete=models.CASCADE)
    ref_unidad_medica = models.TextField()
    cve_presupuestal = models.TextField(primary_key=True)
    cve_nivel_atencion = models.IntegerField()
    cve_unidad_clues = models.ForeignKey(
        NecUnidadMedicaClues, on_delete=models.CASCADE, null=True, blank=True)
    cve_clues = models.TextField(null=True, blank=True)

class NecMedicamento(models.Model):
    cve_medicamento = models.TextField(primary_key=True)
    des_medicamento = models.TextField()

class NecTipoPrescripcion(models.Model):
    cve_tipo_prescripcion = models.TextField(primary_key=True)
    des_tipo_prescripcion = models.TextField()

class NecCie10(models.Model):
    cve_cie10 = models.TextField(primary_key=True)
    des_cie10 = models.TextField()

class NetAtencionNotaMedica(models.Model):
    cve_unidad_medica = models.ForeignKey(
        NetUnidadMedica, on_delete=models.CASCADE)
    stp_fecha_atencion = models.DateTimeField()
    cve_idee_fecha_atencion = models.TextField(primary_key=True)
    ref_cedula = models.TextField()
    cve_idee = models.TextField()

class NetDiagnostico(models.Model):
    cve_idee_fecha_atencion = models.ForeignKey(
        NetAtencionNotaMedica, on_delete=models.CASCADE)
    cve_cie10 = models.ForeignKey(
        NecCie10, on_delete=models.CASCADE)

class NetDiagnosticoTipodx(models.Model):
    cve_idee_fecha_atencion = models.ForeignKey(
        NetDiagnostico, on_delete=models.CASCADE)
    cve_cie10 = models.ForeignKey(
        NecCie10, on_delete=models.CASCADE)
    cve_tipo_diagnostico = models.IntegerField()

class NetPrescripcionMedicamento(models.Model):
    cve_folio_receta = models.TextField(primary_key=True)
    fec_receta = models.DateTimeField()
    cve_medicamento = models.ForeignKey(
        NecMedicamento, on_delete=models.CASCADE)
    can_cantidad = models.IntegerField()
    cve_idee_fecha_atencion = models.ForeignKey(
        NetAtencionNotaMedica, on_delete=models.CASCADE)
    cve_codigo_tipo_receta = models.ForeignKey(
        NecTipoPrescripcion, on_delete=models.CASCADE)
    fec_cancelacion = models.DateTimeField(null=True, blank=True)
    cve_folio_receta_resurtible = models.TextField(null=True, blank=True)
    can_surtir = models.IntegerField(null=True, blank=True)

class NetAsignacion(models.Model):
    cve_asignacion = models.TextField(primary_key=True)
    ref_cedula = models.TextField()
    cve_unidad_medica = models.ForeignKey(
        NetUnidadMedica, on_delete=models.CASCADE)
    cve_matricula = models.TextField()
    cve_especialidad = models.TextField()
    fec_baja = models.DateTimeField(null=True, blank=True)

class NetPersonalOperativo(models.Model):
    cve_matricula = models.TextField(primary_key=True)
    ref_apellido_paterno = models.TextField()
    ref_apellido_materno = models.TextField()
    ref_nombre = models.TextField()

class NecEspecialidad(models.Model):
    cve_especialidad = models.TextField(primary_key=True)
    des_especialidad = models.TextField()

class NetEventoPrescripcion(models.Model):
    cve_idee_fecha_atencion = models.ForeignKey(
        NetAtencionNotaMedica, on_delete=models.CASCADE, primary_key=True)
    cve_asignacion = models.ForeignKey(
        NetAsignacion, on_delete=models.CASCADE)
    stp_evento = models.DateTimeField()


