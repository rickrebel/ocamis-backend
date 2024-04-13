from rest_framework import routers
from django.urls import path, include
from data_param.api.views import FileControlViewSet, NameColumnViewSet
from task.views import AWSErrors

router = routers.DefaultRouter()

router.register(r'file_control', FileControlViewSet)
router.register(r'name_column', NameColumnViewSet)

urlpatterns = [
    # url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    path('', include(router.urls)),
]


