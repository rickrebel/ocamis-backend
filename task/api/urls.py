from django.urls import path, include
from rest_framework import routers
from task.api.views import (
    AsyncTaskViewSet, CutOffViewSet, StepViewSet, ActivityView,
    OfflineTaskViewSet)
from task.main_views_aws import AWSErrors, AWSSuccess, AWSMessage
from task.api.views_channel import MessageSendAPIView

router = routers.DefaultRouter()

router.register(r'async_task', AsyncTaskViewSet)
router.register(r'cut_off', CutOffViewSet)
router.register(r'step', StepViewSet)
router.register(r'offline_task', OfflineTaskViewSet)

urlpatterns = (
    path('activity/', ActivityView.as_view()),
    path('error_aws/', AWSErrors.as_view()),
    path('success_aws/', AWSSuccess.as_view()),
    path('send_socket_example/', MessageSendAPIView.as_view()),
    path('webhook_aws/', AWSMessage.as_view()),
    path('', include(router.urls)),
)
