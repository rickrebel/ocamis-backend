from . import serializers
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)
from desabasto.api.views import StandardResultsSetPagination

from formula.models import Drug, MotherDrugPriority, MotherDrugTotals


class DrugViewSet(ListRetrieveUpdateMix):

    permission_classes = (permissions.AllowAny,)
    queryset = MotherDrugPriority.objects.all()
    serializer_class = serializers.MotherDrugPrioritySerializer

    action_serializers = {
        'list': serializers.MotherDrugPrioritySerializer,
    }

    @action(methods=["post"], detail=False)
    def spiral(self, request):
        from django.db.models import Count, F, Sum
        from geo.models import Delegation, CLUES, Entity
        from medicine.models import Component

        entity_id = request.data.get('entity', 55)
        delegation_id = request.data.get('delegation', None)
        by_delegation = request.data.get('by_delegation', False)
        display_totals = request.data.get('display_totals', False)
        clues_id = request.data.get('clues', None)
        if not clues_id and not delegation_id and not entity_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        component_id = request.data.get('component', 96)
        presentation_id = request.data.get('presentation', None)
        container_id = request.data.get('container', None)
        if not container_id and not presentation_id and not component_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        query_filter = {"entity_week__iso_year__gte": 2017}
        if clues_id:
            query_filter['clues_id'] = clues_id
        elif delegation_id:
            query_filter['delegation_id'] = delegation_id
        elif entity_id:
            query_filter['entity_week__entity_id'] = entity_id
        filter_totals = query_filter.copy()

        if container_id:
            query_filter['container_id'] = container_id
        elif presentation_id:
            query_filter['container__presentation_id'] = presentation_id
        elif component_id:
            query_filter['container__presentation__component_id'] = component_id

        first_values = {
            'iso_week': 'entity_week__iso_week',
            'iso_year': 'entity_week__iso_year',
        }
        if by_delegation:
            first_values['delegation'] = 'delegation_id'
        annotates = {
            'total': Sum('total'),
            'delivered': Sum('delivered_total'),
            'prescribed': Sum('prescribed_total'),
        }
        for key, value in first_values.items():
            annotates[key] = F(value)
        display_values = [v for v in annotates.keys()]
        order_values = ["iso_year", "iso_week"]
        if by_delegation:
            order_values.insert(0, "delegation")

        drugs = MotherDrugPriority.objects\
            .filter(**query_filter)\
            .prefetch_related('entity_week') \
            .values(*first_values.values()) \
            .annotate(**annotates) \
            .values(*display_values) \
            .order_by(*order_values)

        data = {
            'drugs': list(drugs),
        }

        if display_totals:
            totals = MotherDrugTotals.objects\
                .filter(**filter_totals)\
                .values(*first_values.values()) \
                .annotate(**annotates) \
                .values(*display_values) \
                .order_by(*order_values)
            data['totals'] = list(totals)

        return Response(data, status=status.HTTP_200_OK)
