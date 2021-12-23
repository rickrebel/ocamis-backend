from django.urls import re_path, include
from rest_framework import routers
from rest_framework.authtoken import views


router = routers.DefaultRouter()

urlpatterns = [
    re_path(
        r'^api-auth/',
        include(
            'rest_framework.urls',
            namespace='rest_framework'
        )
    ),
    re_path(r'^token-auth/', views.obtain_auth_token),

    # Endpoints
    re_path(r'^desabasto/', include('desabasto.api.urls')),
]
