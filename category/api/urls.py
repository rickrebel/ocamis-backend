from rest_framework import routers
from django.urls import path, include


router = routers.DefaultRouter()

urlpatterns = (
    # path(r'^commitmentgroup/$', FileTypeSimpleSerializer.as_view()),
    path('', include(router.urls)),
)
