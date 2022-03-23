# -*- coding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals
#from celery import shared_task, task


class Empty_:
    pass


#@shared_task
def create_report_insumos_y_reportes():
    from report.api.views import ReportExportView2
    temporal_report = ReportExportView2()
    request = Empty_()
    request.query_params = {}
    response_ = temporal_report.get(request)


#@shared_task
def create_report_insumos_y_reportes_publico():
    from report.api.views import PublicReportExportView2
    temporal_report = PublicReportExportView2()
    request = Empty_()
    request.query_params = {}
    response_ = temporal_report.get(request)
