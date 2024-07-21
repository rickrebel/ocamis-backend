from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from inai.admin import ocamis_admin_site
from email_sendgrid.admin import email_admin_site


admin.site.site_header = "Administración Catálogos OCAMIS"
admin.site.site_title = "Administración Catálogos OCAMIS"
admin.site.index_title = "Administración Catálogos OCAMIS"


urlpatterns = [
    path('', lambda request: redirect('admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('ocamis_admin/', ocamis_admin_site.urls),
    path('email_admin/', email_admin_site.urls),
    path('api/', include("api.urls")),
    path('sendgrid/', include('email_sendgrid.urls')),
    #path(r'^ckeditor/', include('ckeditor_uploader.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns.append(re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT}))
    urlpatterns.append(re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT}))
