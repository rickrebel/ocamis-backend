# -*- coding: utf-8 -*-
from core.api.views import (
    CatalogView, CatalogViz, CatalogShortageViz, CatalogComponents)
#from api.views import CatalogView
from django.urls import path

urlpatterns = [
    path('dashboard_catalog/', CatalogView.as_view()),
    path('viz_catalog/', CatalogViz.as_view()),
    path('viz_shortage_catalog/', CatalogShortageViz.as_view()),
    path('viz_components/', CatalogComponents.as_view()),
]
