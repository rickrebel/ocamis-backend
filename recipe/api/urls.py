from rest_framework import routers
from django.conf.urls import url, include

router = routers.DefaultRouter()

urlpatterns = [
    url('', include(router.urls)),
]
