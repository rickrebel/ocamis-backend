from . import serializers
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)

from mat.models import (
    MotherDrugPriority, MotherDrug, MotherDrugTotals, MotherDrugEntity)
from formula.models import (
    MatDrugTotals, MatDrug, MatDrugPriority, MatDrugEntity)


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
        # print("Spiral")
        from django.conf import settings
        from django.db.models import F, Sum
        from django.apps import apps
        from medicine.models import Component
        is_big_active = getattr(settings, "IS_BIG_ACTIVE", False)
        provider_id = request.data.get('provider')
        delegation_id = request.data.get('delegation', None)
        by_delegation = request.data.get('by_delegation', False)
        display_totals = request.data.get('display_totals', False)
        clues_id = request.data.get('clues', None)

        group_by = request.data.get('group_by', None)
        # by_year = group_by == 'iso_year'

        component_id = request.data.get('component', 96)
        components_ids = request.data.get('components', [])
        presentation_id = request.data.get('presentation', None)
        container_id = request.data.get('container', None)
        therapeutic_group_id = request.data.get('therapeutic_group', None)

        some_geo = clues_id or delegation_id or provider_id
        some_drug = container_id or presentation_id or component_id
        if group_by == 'iso_year':
            if not some_geo or not some_drug:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'provider':
            if not some_drug:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'delegation':
            by_delegation = True
            if not some_drug or not provider_id:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'therapeutic_group':
            if not some_geo:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    'errors': 'Se requiere una institución para desplegar los datos por grupo terapéutico'
                })
        elif group_by == 'component':
            if not some_geo or (not therapeutic_group_id and not components_ids):
                required = []
                if not some_geo:
                    required.append('una institución')
                if not therapeutic_group_id and not components_ids:
                    required.append(
                        'un grupo terapéutico o una selección de componentes')
                error_message = 'Se requiere ' + ' y '.join(required)
                error_message += ' para desplegar los datos por componente'
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    'warning': error_message
                })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        has_delegation = True
        if component_id:
            try:
                component = Component.objects.get(id=component_id)
                has_delegation = component.priority < 5
            except Component.DoesNotExist:
                has_delegation = False

        if group_by == 'component' or group_by == 'therapeutic_group':
            has_delegation = False

        if not has_delegation:
            if clues_id or by_delegation or delegation_id:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    'errors': 'No se puede desagregar la información por '
                              'delegación para este componente'
                })

        def build_query(is_total=False):
            # is_complex = is_total or bool(clues_id)
            is_complex = True
            is_mini = not is_total and not has_delegation
            prefetches = []
            if not is_mini:
                prefetches = ['week_record']

            prev_iso = "" if is_mini else "week_record__"

            first_values = {
                'iso_week': f'{prev_iso}iso_week',
                'iso_year': f'{prev_iso}iso_year',
                'year': f'{prev_iso}year',
                'month': f'{prev_iso}month',
            }
            comp_string = "medicament__container__presentation__component"
            if is_mini:
                field_ent = "entity_id"
            else:
                field_ent = f"{prev_iso}provider_id"
            if is_mini:
                field_comp = f"{comp_string}_id"
            elif is_complex:
                field_comp = 'container__presentation__component_id'
            else:
                field_comp = 'component_id'

            query_filter = {f"{prev_iso}iso_year__gte": 2017}
            if clues_id:
                query_filter['clues_id'] = clues_id
            elif delegation_id:
                query_filter['delegation_id'] = delegation_id
            elif provider_id:
                first_values['provider'] = field_ent
                query_filter[field_ent] = provider_id

            if group_by == 'provider':
                first_values['provider'] = field_ent
            elif by_delegation:
                first_values["delegation"] = "delegation_id"
            elif group_by == 'therapeutic_group':
                if not is_total:
                    first_values['therapeutic_group'] = f"{comp_string}__groups__id"
                    # query_filter[f'{comp_string}__groups__id'] = therapeutic_group_id
            elif group_by == 'component':
                if not is_total:
                    if components_ids:
                        query_filter[f'{comp_string}__id__in'] = components_ids
                    else:
                        query_filter[f'{comp_string}__groups__id'] = therapeutic_group_id
                        query_filter[f'{comp_string}__priority__lt'] = 6
                    first_values['component'] = field_comp

            prev_med = "medicament__" if is_mini else ""
            # container__presentation__component
            # container__presentation
            if is_total:
                pass
            # RICK Deshacer este orden
            elif container_id:
                query_filter[f'{prev_med}container_id'] = container_id
            elif presentation_id:
                if is_mini:
                    field = 'medicament__container__presentation_id'
                elif is_complex:
                    field = 'container__presentation_id'
                else:
                    field = 'presentation_id'
                query_filter[field] = presentation_id
            elif component_id:
                if is_mini:
                    field = 'medicament__container__presentation__component_id'
                elif is_complex:
                    field = 'container__presentation__component_id'
                else:
                    field = 'component_id'
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
            order_values = ["year", "month", "iso_year", "iso_week"]
            if by_delegation:
                order_values.insert(0, "delegation")

            prev_model = "Mother" if is_big_active else "Mat"
            # model = "Totals" if is_total else "Priority"
            if is_total:
                model = "Totals"
            elif is_mini:
                model = "Entity"
            else:
                model = "Priority"
            # model = "Totals" if is_total else "Entity"
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
