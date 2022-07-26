# -*- coding: utf-8 -*-
from core.api.views import CatalogView
#from api.views import CatalogView
from django.urls import path

urlpatterns = [
    path('dashboard_catalog/', CatalogView.as_view()),
]
