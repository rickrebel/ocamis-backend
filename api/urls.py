from django.urls import re_path, include
from rest_framework import routers
from rest_framework.authtoken import views
#from user_profile.api.views import UserLoginAPIView


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
    re_path(r'^auth/', include('auth.api.urls')),
    re_path(r'^desabasto/', include('desabasto.api.urls')),
    re_path(r'^catalog/', include('catalog.api.urls')),
    re_path(r'^medicine/', include('medicine.api.urls')),
    re_path(r'^report/', include('report.api.urls')),
    re_path(r'^formula/', include('formula.api.urls')),
    re_path(r'^inai/', include('inai.api.urls')),
    re_path(r'^', include('core.api.urls')),
]
