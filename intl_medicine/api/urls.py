from django.urls import path, include
from rest_framework import routers
from intl_medicine.api.views import RespondentViewSet, GroupAnswerViewSet

router = routers.DefaultRouter()

router.register(r'respondent', RespondentViewSet)
# router.register(r'group', GroupViewSet)
router.register(r'group_answer', GroupAnswerViewSet)

urlpatterns = (
    path('', include(router.urls)),
)
