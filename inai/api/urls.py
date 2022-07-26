from rest_framework import routers
from django.conf.urls import url, include

"""from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason)
from .views import FileControlViewSet"""

router = routers.DefaultRouter()
#router.register(r'file_control', FileControlViewSet)

urlpatterns = [
    #url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
