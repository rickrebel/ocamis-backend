# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.core.validators import validate_email
from django.db import models


class PurchaseRaw(models.Model):
    raw_pdf = models.TextField(blank=True, null=True)
    orden = models.CharField(
        max_length=30, blank=True, null=True)
    contrato = models.CharField(
        max_length=70, blank=True, null=True)
    procedimiento = models.CharField(
        max_length=30, blank=True, null=True)
    partida_presupuestal = models.CharField(
        max_length=50, blank=True, null=True)
    rfc = models.CharField(
        max_length=15, blank=True, null=True)
    preveedor = models.TextField(blank=True, null=True)
    expedition_date = models.CharField(
        max_length=10, blank=True, null=True)
    deliver_date = models.CharField(
        max_length=10, blank=True, null=True)
    warehouse = models.TextField(blank=True, null=True)
    adress_warehouse = models.TextField(blank=True, null=True)
    item = models.IntegerField(blank=True, null=True)
    clave_insumo = models.CharField(
        max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    clues = models.TextField(blank=True, null=True)
    entidad = models.CharField(
        max_length=80, blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = u"Orden de Suministro"
        verbose_name_plural = u"Ordenes de Suministro"

    def __str__(self):
        return self.orden or 'none'
