from rest_framework import routers
from django.conf.urls import url, include

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason)
#from inai.api.views import FileControlViewSet, PetitionViewSet
from inai.api.views import (
    FileControlViewSet, PetitionViewSet, ProcessFileViewSet)

router = routers.DefaultRouter()
router.register(r'petition', PetitionViewSet)
#router.register(r'clues', FileControlViewSet)
router.register(
    r'^petition/(?P<petition_id>[-\d]+)/process_file', ProcessFileViewSet)

urlpatterns = [
    #url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
