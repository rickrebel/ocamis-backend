from rest_framework import routers
from django.conf.urls import url, include


from files_categories.models import (
    TypeFile, StatusControl, ColumnType, NegativeReason)

router = routers.DefaultRouter()

urlpatterns = [
    #url(r'^commitmentgroup/$', TypeFileSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
