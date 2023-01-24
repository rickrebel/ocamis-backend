from rest_framework import routers
from django.urls import path, include

from medicine.api.views import (
    ComponentList,
    GroupList,
    PresentationTypeList,
    PresentationList,
    ContainerList,
)

router = routers.DefaultRouter()
router.register(r'component', ComponentList)
router.register(r'group', GroupList)
router.register(r'presentation_type', PresentationTypeList)
router.register(r'presentation', PresentationList)
router.register(r'container', ContainerList)


urlpatterns = [
    path('', include(router.urls)),
]
