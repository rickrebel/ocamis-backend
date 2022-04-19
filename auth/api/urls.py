from rest_framework import routers
from django.conf.urls import url, include

from auth.api.views import UserRegistrationAPIView, UserLoginAPIView

#from auth.api.views import UserViewSet


router = routers.DefaultRouter()
#router.register(r'users', UserViewSet)
#router.register(r'settings', SettingsViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^register/$', UserRegistrationAPIView.as_view(), name='register'),
    url(r'^login/$', UserLoginAPIView.as_view(), name='login'),
]
