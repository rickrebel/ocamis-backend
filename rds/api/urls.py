from rest_framework import routers
from django.urls import path, include

from rds.api.views import ClusterViewSet

router = routers.DefaultRouter()

router.register(r'cluster', ClusterViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

