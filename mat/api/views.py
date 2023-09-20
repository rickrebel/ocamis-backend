from . import serializers
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)
# from desabasto.api.views import StandardResultsSetPagination

from mat.models import MotherDrugPriority, MotherDrug, MotherDrugTotals
from formula.models import MatDrugTotals, MatDrug, MatDrugPriority


class DrugViewSet(ListRetrieveUpdateMix):

    permission_classes = (permissions.AllowAny,)
    queryset = MotherDrugPriority.objects.all()
    # queryset = MotherDrug.objects.all()
    serializer_class = serializers.MotherDrugPrioritySerializer
    # serializer_class = serializers.MotherDrugSerializer

    action_serializers = {
        'list': serializers.MotherDrugPrioritySerializer,
        # 'list': serializers.MotherDrugSerializer,
    }

    @action(methods=["post"], detail=False)
    def spiral(self, request):
        from django.conf import settings
        from django.db.models import Count, F, Sum
        from django.apps import apps
        # from geo.models import Delegation, CLUES, Entity
        # from medicine.models import Component
        is_big_active = getattr(settings, "IS_BIG_ACTIVE")
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

        def build_query(is_total=False):
            # is_complex = is_total or bool(clues_id)
            is_complex = True

            prefetches = ['entity_week'] if is_complex else []

            prev_iso = "entity_week__" if is_complex else ""
            query_filter = {f"{prev_iso}iso_year__gte": 2017}
            if clues_id:
                query_filter['clues_id'] = clues_id
            elif delegation_id:
                query_filter['delegation_id'] = delegation_id
            elif entity_id:
                field = f"{prev_iso}entity_id"
                query_filter[field] = entity_id

            if is_total:
                pass
            elif container_id:
                query_filter['container_id'] = container_id
            elif presentation_id:
                field = 'container__presentation_id' \
                    if is_complex else 'presentation_id'
                query_filter[field] = presentation_id
            elif component_id:
                field = 'container__presentation__component_id' \
                    if is_complex else 'component_id'
                query_filter[field] = component_id

            first_values = {
                'iso_week': f'{prev_iso}iso_week',
                'iso_year': f'{prev_iso}iso_year',
            }
            if by_delegation:
                first_values["delegation"] = "delegation_id"
            annotates = {
                'total': Sum('total'),
                'delivered': Sum('delivered_total'),
                'prescribed': Sum('prescribed_total'),
            }
            display_values = [v for v in annotates.keys()]
            for key, value in first_values.items():
                if key != value:
                    annotates[key] = F(value)
                display_values.append(key)
            order_values = ["iso_year", "iso_week"]
            if by_delegation:
                order_values.insert(0, "delegation")

            prev_model = "Mother" if is_big_active else "Mat"
            if is_total:
                model_name = f"{prev_model}DrugTotals"
            else:
                # model_name = "MotherDrug" if is_complex else "MotherDrugExtended"
                model_name = f"{prev_model}DrugPriority"
            print("model_name: ", model_name)
            app_label = "mat" if is_big_active else "formula"
            mother_model = apps.get_model(app_label, model_name)

            return mother_model.objects\
                .filter(**query_filter)\
                .prefetch_related(*prefetches)\
                .values(*first_values.values()) \
                .annotate(**annotates) \
                .values(*display_values) \
                .order_by(*order_values)

        data = {'drugs': list(build_query())}

        if display_totals:
            data['totals'] = list(build_query(is_total=True))

        return Response(data, status=status.HTTP_200_OK)
