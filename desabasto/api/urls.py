from rest_framework import routers
from django.conf.urls import url, include

"""rom desabasto.api.views import (
    CatalogView,
    # StateList,
    InstitutionList,
    CLUESList,
    SupplyList,
    ReportView, ReportExportView, PublicReportExportView,
    ReportList, ComponentList, ReportStateInstitutionCountList,


    GroupList,
    PresentationTypeList,
    PresentationList,
    ContainerList,

    SendEmailNewOrganizationView, ReportMedicineView
)"""

router = routers.DefaultRouter()
"""router.register(r'report', ReportView)
router.register(r'component', ComponentList)
# router.register(r'states', StateList)
router.register(r'institutions', InstitutionList)
router.register(r'clues', CLUESList)
router.register(r'supplies', SupplyList)

router.register(r'group', GroupList)
router.register(r'presentation_type', PresentationTypeList)
router.register(r'presentation', PresentationList)
router.register(r'container', ContainerList)""
"""

"""url(r'^new_organization/$', SendEmailNewOrganizationView.as_view()),
url(r'^medicine_report/$', ReportMedicineView.as_view()),
url(r'^export/$', ReportExportView.as_view()),
url(r'^reports/$', ReportList.as_view()),
url(r'^reports/state_count/$', ReportStateInstitutionCountList.as_view()),
url(r'^public_export/$', PublicReportExportView.as_view()),
# url(r'^reports/$', ReportListView.as_view()),
url(r'^catalog/$', CatalogView.as_view()),"""
urlpatterns = [
    url('', include(router.urls)),
]
