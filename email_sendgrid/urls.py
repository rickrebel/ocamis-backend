from django.urls import re_path
from .views import SendGridWebhook

urlpatterns = [
    re_path(r'^webhook/$', SendGridWebhook.as_view()),
    re_path(
        r'^webhook/(?P<webhook_slug>[-\w]+)/?$',
        SendGridWebhook.as_view()
    ),
]
