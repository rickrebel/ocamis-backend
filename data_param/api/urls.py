from rest_framework import routers
from django.urls import path, include
from data_param.api.views import (FileControlViewSet)
from task.views import AWSErrors

router = routers.DefaultRouter()

router.register(r'file_control', FileControlViewSet)

urlpatterns = [
    # url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    path('', include(router.urls)),
]


