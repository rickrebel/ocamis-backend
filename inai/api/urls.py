from rest_framework import routers
from django.urls import path, include

#from inai.api.views import FileControlViewSet, PetitionViewSet
from inai.api.views import (
    FileControlViewSet, PetitionViewSet, ProcessFileViewSet,
    AscertainableViewSet, PetitionFileControlViewSet)

from inai.api.views_aws import (
    DataFileViewSet, OpenDataInaiViewSet, AutoExplorePetitionViewSet,
    AsyncTaskViewSet)
from inai.api.views_channel import MessageSendAPIView

from inai.views import (AWSMessage, AWSErrors)


router = routers.DefaultRouter()
router.register(r'petition', PetitionViewSet)
router.register(
    r'^petition_file_control/(?P<petition_file_control_id>[-\d]+)/data_file',
    AscertainableViewSet)
router.register(r'petition_file_control', PetitionFileControlViewSet)
router.register(r'file_control', FileControlViewSet)
router.register(r'data_file', DataFileViewSet)
router.register(r'async_task', AsyncTaskViewSet)

router.register(r'open_data_inai', OpenDataInaiViewSet)
#router.register(r'petition', PetitionViewSet)
router.register(r'auto_explore', AutoExplorePetitionViewSet)
#router.register(r'some-url-name', views.SomeViewSet, basename='index')
#router.register(r'clues', FileControlViewSet)
router.register(
    r'^petition/(?P<petition_id>[-\d]+)/process_file', ProcessFileViewSet)

urlpatterns = (
    path('suscription_test', AWSErrors.as_view()),
    path('send_socket_example/', MessageSendAPIView.as_view()),
    path('webhook_aws/', AWSMessage.as_view()),
    path('', include(router.urls)),
)
