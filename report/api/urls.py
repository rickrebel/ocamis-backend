from rest_framework import routers
# from django.urls import path
from django.urls import path

from report.api.views import (
    SupplyList, SupplyList2,
    ReportView, ReportExportView, PublicReportExportView,
    ReportList, ReportStateInstitutionCountList,
    ReportMedicineView, CatalogView,
    CovidReportView2, ComplementReportView, ReportView2,
    ReportExportView2, CovidReportExportView2, CovidReportExportView,
    PublicReportExportView2, RelatosList, DinamicList
)

router = routers.DefaultRouter()
router.register(r'supplies', SupplyList)
router.register(r'covid', CovidReportView2)
router.register(r'complement', ComplementReportView)
router.register(r'medicine', ReportView2)
# router.register(r'export2', ReportExportView2)
router.register(r"", ReportView)

urlpatterns = [
    path('catalog/', CatalogView.as_view()),
    path('medicine_report/', ReportMedicineView.as_view()),
    path('export/', ReportExportView.as_view()),
    path('export_covid/', CovidReportExportView.as_view()),
    # url(r'^covid/$', CovidReportView.as_view()),
    # re_url(r'^new_covid/$', CovidReportView3, name="new-covid"),
    path('reports/', ReportList.as_view()),
    path('all_supplies/', SupplyList2.as_view()),
    path('state_count/', ReportStateInstitutionCountList.as_view()),
    path('public_export/', PublicReportExportView.as_view()),
    path('generate_public/', PublicReportExportView2.as_view()),
    # path(r'^reports/$', ReportListView.as_view()),
    path('generate_export/', ReportExportView2.as_view()),
    path('generate_export_covid/', CovidReportExportView2.as_view()),
    path('shiny/narrations/', RelatosList.as_view()),
    path('shiny/<str:group_name>/', DinamicList.as_view()),
]

urlpatterns += router.urls
# print("urlpatterns")
# (urlpatterns)
