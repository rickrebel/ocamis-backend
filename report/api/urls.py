from rest_framework import routers
#from django.urls import path
from django.conf.urls import url

from report.api.views import (
    SupplyList,
    ReportView, ReportExportView, PublicReportExportView,
    ReportList, ReportStateInstitutionCountList,
    ReportMedicineView, CatalogView,
    CovidReportView2, ComplementReportView, ReportView2,
    ReportExportView2, CovidReportExportView2, CovidReportExportView,
    PublicReportExportView2
)

router = routers.DefaultRouter()
router.register(r'supplies', SupplyList)
router.register(r'covid', CovidReportView2)
router.register(r'complement', ComplementReportView)
router.register(r'medicine', ReportView2)
#router.register(r'export2', ReportExportView2)
router.register(r"", ReportView)

urlpatterns = [
    url(r'^catalog/$', CatalogView.as_view()),
    url(r'^medicine_report/$', ReportMedicineView.as_view()),
    url(r'^export/$', ReportExportView.as_view()),
    url(r'^export_covid/$', CovidReportExportView.as_view()),
    #url(r'^covid/$', CovidReportView.as_view()),
    #re_url(r'^new_covid/$', CovidReportView3, name="new-covid"),
    #url(r'reports/$', ReportList.as_view()),
    url(r'^state_count/$', ReportStateInstitutionCountList.as_view()),
    url(r'^public_export/$', PublicReportExportView.as_view()),
    url(r'^generate_public/$', PublicReportExportView2.as_view()),
    #path(r'^reports/$', ReportListView.as_view()),
    url(r'^generate_export/$', ReportExportView2.as_view()),
    url(r'^generate_export_covid/$', CovidReportExportView2.as_view()),

]

urlpatterns += router.urls
#print("urlpatterns")
#print(urlpatterns)
