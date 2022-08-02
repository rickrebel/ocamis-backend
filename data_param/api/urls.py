from rest_framework import routers
from django.conf.urls import url, include

router = routers.DefaultRouter()

urlpatterns = [
    #url(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    url('', include(router.urls)),
]
