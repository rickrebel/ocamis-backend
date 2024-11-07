from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions
from rest_framework.filters import SearchFilter

from medicine.api.component.serializers import (
    FullComponentSerializer, FullContainerSerializer,
    FullPresentationSerializer
)
from medicine.models import Component, Presentation, Container


class MediumPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class DefaultViewSet(ModelViewSet):
    pagination_class = MediumPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    filter_backends = [SearchFilter]


class ComponentViewSet(DefaultViewSet):
    queryset = Component.objects.all()
    serializer_class = FullComponentSerializer
    search_fields = ["name"]


class PresentationViewSet(DefaultViewSet):
    queryset = Presentation.objects.all()
    serializer_class = FullPresentationSerializer
    search_fields = ["description", "presentation_type_raw"]


class ContainerViewSet(DefaultViewSet):
    queryset = Container.objects.all()
    serializer_class = FullContainerSerializer
    search_fields = ["name", "key"]
