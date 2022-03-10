from rest_framework import routers
from django.conf.urls import url, include

from catalog.api.views import (
    # StateList,
    InstitutionList,
    CLUESList,
    SendEmailNewOrganizationView,
    StateViewSet,
)

router = routers.DefaultRouter()
# router.register(r'states', StateList)
router.register(r'institutions', InstitutionList)
router.register(r'clues', CLUESList)
router.register(r'state', StateViewSet)

urlpatterns = [
    url(r'^new_organization/$', SendEmailNewOrganizationView.as_view()),
    url('', include(router.urls)),
]
