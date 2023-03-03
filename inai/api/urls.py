from rest_framework import routers
from django.urls import path, include

#from inai.api.views import FileControlViewSet, PetitionViewSet
from inai.api.views import (
    PetitionViewSet, ReplyFileViewSet,
    AscertainableViewSet, PetitionFileControlViewSet)

from inai.api.views_aws import (
    DataFileViewSet, OpenDataInaiViewSet, AutoExplorePetitionViewSet)


router = routers.DefaultRouter()
router.register(r'petition', PetitionViewSet)
router.register(
    r'^petition_file_control/(?P<petition_file_control_id>[-\d]+)/data_file',
    AscertainableViewSet)
router.register(r'petition_file_control', PetitionFileControlViewSet)
# RICK 17: Mover de lugar
router.register(r'data_file', DataFileViewSet)

router.register(r'open_data_inai', OpenDataInaiViewSet)
router.register(r'auto_explore', AutoExplorePetitionViewSet)
router.register(
    r'^petition/(?P<petition_id>[-\d]+)/process_file', ReplyFileViewSet)

urlpatterns = (
    path('', include(router.urls)),
)
