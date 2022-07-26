from rest_framework import routers
from django.conf.urls import url, include

from files_categories.models import (
    TypeFile, StatusControl, ColumnType, NegativeReason)
from .views import GroupFileViewSet

router = routers.DefaultRouter()
router.register(r'group_file', GroupFileViewSet)

urlpatterns = [
    #url(r'^commitmentgroup/$', TypeFileSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
