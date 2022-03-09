from rest_framework import routers
from django.conf.urls import url, include

from desabasto.api.views import CatalogView

router = routers.DefaultRouter()
"""url(r'^new_organization/$', SendEmailNewOrganizationView.as_view()),
url(r'^medicine_report/$', ReportMedicineView.as_view()),
url(r'^export/$', ReportExportView.as_view()),
url(r'^reports/$', ReportList.as_view()),
url(r'^reports/state_count/$', ReportStateInstitutionCountList.as_view()),
url(r'^public_export/$', PublicReportExportView.as_view()),
url(r'^reports/$', ReportListView.as_view()),"""
url(r'^catalog/$', CatalogView.as_view()),
urlpatterns = [
    url('', include(router.urls)),
]
