"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from inai.admin import ocamis_admin_site


admin.site.site_header = "Administración Cero Desabasto"
admin.site.site_title = "Administración Cero Desabasto"
admin.site.index_title = "Administración Cero Desabasto"


urlpatterns = [
    path('', lambda request: redirect('admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('ocamis_admin/', ocamis_admin_site.urls),
    path('api/', include("api.urls")),
    path('sendgrid/', include('email_sendgrid.urls')),
    #path(r'^ckeditor/', include('ckeditor_uploader.urls')),
]
#+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns.append(path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT}))
    urlpatterns.append(path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT}))
