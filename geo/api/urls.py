from rest_framework import routers
from django.urls import path, include

from geo.api.views import (
    # StateList,
    InstitutionList,
    CLUESList,
    SendEmailNewOrganizationView,
    StateViewSet,
    AgencyViewSet,
    EntityViewSet
)

router = routers.DefaultRouter()
# router.register(r'states', StateList)
router.register(r'institutions', InstitutionList)
router.register(r'clues', CLUESList)
router.register(r'state', StateViewSet)
router.register(r'agency', AgencyViewSet)
router.register(r'entity', EntityViewSet)

urlpatterns = [
    path('new_organization/', SendEmailNewOrganizationView.as_view()),
    path('', include(router.urls)),
]
