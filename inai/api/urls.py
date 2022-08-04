from rest_framework import routers
from django.conf.urls import url, include

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason)
#from inai.api.views import FileControlViewSet, PetitionViewSet
from inai.api.views import (
    FileControlViewSet, PetitionViewSet, ProcessFileViewSet,
    AscertainableViewSet, PetitionFileControlViewSet)

from inai.api.views_aws import (DataFileViewSet)

router = routers.DefaultRouter()
router.register(r'petition', PetitionViewSet)
router.register(
    r'^petition_file_control/(?P<petition_file_control_id>[-\d]+)/data_file',
    AscertainableViewSet)
router.register(r'petition_file_control', PetitionFileControlViewSet)
router.register(r'file_control', FileControlViewSet)
router.register(r'data_file', DataFileViewSet)
#router.register(r'some-url-name', views.SomeViewSet, basename='index')
#router.register(r'clues', FileControlViewSet)
router.register(
    r'^petition/(?P<petition_id>[-\d]+)/process_file', ProcessFileViewSet)

urlpatterns = [
    #url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
