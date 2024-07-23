from rest_framework import routers
from django.urls import path, include

# from inai.api.views import FileControlViewSet, PetitionViewSet
from respond.api.views import SheetFileViewSet
from inai.api.views_aws import AutoExplorePetitionViewSet
from respond.api.views_aws import DataFileViewSet

router = routers.DefaultRouter()

router.register(r'data_file', DataFileViewSet)
router.register(r'sheet_file', SheetFileViewSet)
router.register(r'auto_explore', AutoExplorePetitionViewSet)

urlpatterns = (
    path('', include(router.urls)),
)
