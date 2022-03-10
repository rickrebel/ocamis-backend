from rest_framework import routers
from django.conf.urls import url, include

from report.api.views import (
    SupplyList,
    ReportView, ReportExportView, PublicReportExportView,
    ReportList, ReportStateInstitutionCountList,
    ReportMedicineView, CatalogView, CovidReportView
    #ReportListView,
)

router = routers.DefaultRouter()
#router.register(r'report', ReportView)
router.register(r"", ReportView)
router.register(r'supplies', SupplyList)
router.register(r'covid', CovidReportView)


urlpatterns = [
    url(r'^catalog/$', CatalogView.as_view()),
    url(r'^medicine_report/$', ReportMedicineView.as_view()),
    url(r'^export/$', ReportExportView.as_view()),
    #url(r'^covid/$', CovidReportView.as_view()),
    url(r'^reports/$', ReportList.as_view()),
    url(r'^state_count/$', ReportStateInstitutionCountList.as_view()),
    url(r'^public_export/$', PublicReportExportView.as_view()),
    #url(r'^reports/$', ReportListView.as_view()),
    url('', include(router.urls)),
]
