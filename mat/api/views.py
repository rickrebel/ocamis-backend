from . import serializers
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)

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
        from django.db.models import F, Sum
        from django.apps import apps
        is_big_active = getattr(settings, "IS_BIG_ACTIVE")
        entity_id = request.data.get('provider')
        delegation_id = request.data.get('delegation', None)
        by_delegation = request.data.get('by_delegation', False)
        display_totals = request.data.get('display_totals', False)
        clues_id = request.data.get('clues', None)

        group_by = request.data.get('group_by', None)
        # by_year = group_by == 'iso_year'

        component_id = request.data.get('component', 96)
        presentation_id = request.data.get('presentation', None)
        container_id = request.data.get('container', None)

        some_geo = clues_id or delegation_id or entity_id
        some_drug = container_id or presentation_id or component_id
        if group_by == 'iso_year':
            if not some_geo or not some_drug:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'provider':
            if not some_drug:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'delegation':
            by_delegation = True
            if not some_drug or not entity_id:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'component':
            if not some_geo:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        def build_query(is_total=False):
            # is_complex = is_total or bool(clues_id)
            is_complex = True

            prefetches = ['entity_week'] if is_complex else []

            prev_iso = "entity_week__" if is_complex else ""

            first_values = {
                'iso_week': f'{prev_iso}iso_week',
                'iso_year': f'{prev_iso}iso_year',
            }
            field_ent = f"{prev_iso}entity_id"
            field_comp = 'container__presentation__component_id' \
                if is_complex else 'component_id'

            query_filter = {f"{prev_iso}iso_year__gte": 2017}
            if clues_id:
                query_filter['clues_id'] = clues_id
            elif delegation_id:
                query_filter['delegation_id'] = delegation_id
            elif entity_id:
                first_values['provider'] = field_ent
                query_filter[field_ent] = entity_id

            if group_by == 'provider':
                first_values['provider'] = field_ent
            elif by_delegation:
                first_values["delegation"] = "delegation_id"
            elif group_by == 'component':
                if not is_total:
                    first_values['component'] = field_comp

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
            model = "Totals" if is_total else "Priority"
            model_name = f"{prev_model}Drug{model}"
            # if is_total:
            #     model_name = f"{prev_model}DrugTotals"
            # else:
            #     # model_name = "MotherDrug" if is_complex else "MotherDrugExtended"
            #     model_name = f"{prev_model}DrugPriority"
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
