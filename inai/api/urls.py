from rest_framework import routers
from django.urls import path, include

from inai.api.views import (
    PetitionViewSet, PetitionFileControlViewSet, MonthRecordViewSet,
    RequestTemplateViewSet)
from respond.api.views import ReplyFileViewSet, AscertainableViewSet

from inai.api.views_aws import OpenDataInaiViewSet


router = routers.DefaultRouter()
router.register(r'petition', PetitionViewSet)
router.register(
    r'^petition_file_control/(?P<petition_file_control_id>[-\d]+)/data_file',
    AscertainableViewSet)
router.register(r'petition_file_control', PetitionFileControlViewSet)

router.register(r'month_record', MonthRecordViewSet)
router.register(r'request_template', RequestTemplateViewSet)
router.register(r'open_data_inai', OpenDataInaiViewSet)
router.register(
    r'^petition/(?P<petition_id>[-\d]+)/reply_file', ReplyFileViewSet)

urlpatterns = (
    path('', include(router.urls)),
)
