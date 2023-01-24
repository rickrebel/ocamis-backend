from rest_framework import routers
from django.urls import path, include

from auth.api.views import UserRegistrationAPIView, UserLoginAPIView

#from auth.api.views import UserViewSet


router = routers.DefaultRouter()
#router.register(r'users', UserViewSet)
#router.register(r'settings', SettingsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),
]
