from rest_framework import routers
from django.urls import path, include
from mat.api.views import DrugViewSet

router = routers.DefaultRouter()

router.register(r'drug', DrugViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
