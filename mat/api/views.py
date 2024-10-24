from django.http import HttpResponse
from mat.api.drug_export_utils import DrugExport
# from scripts.storage_utils.save_file import upload_file_to_storage
from xlsx_export.generic import export_xlsx
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
        from medicine.models import Component
        from mat.api.drug_export_utils import DrugExport
        # is_big_active = getattr(settings, "IS_BIG_ACTIVE", False)
        provider_id = request.data.get('provider')
        # delegation_id = request.data.get('delegation', None)
        # by_delegation = request.data.get('by_delegation', False)
        display_totals = request.data.get('display_totals', False)
        # clues_id = request.data.get('clues', None)
        group_by = request.data.get('group_by', None)

        component_id = request.data.get('component')
        components_ids = request.data.get('components', [])
        presentation_id = request.data.get('presentation', None)
        container_id = request.data.get('container', None)
        therapeutic_group_id = request.data.get('therapeutic_group', None)

        # some_geo = clues_id or delegation_id or provider_id
        some_geo = provider_id
        some_drug = container_id or presentation_id or component_id

        if group_by == 'iso_year':
            if not some_geo or not some_drug:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'provider':
            if not some_drug and not therapeutic_group_id:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif group_by == 'delegation':
            # by_delegation = True
            if not provider_id:
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

        # has_delegation = True
        if component_id:
            try:
                Component.objects.get(id=component_id)
                # has_delegation = component.priority < 5
                # has_delegation = False
            except Component.DoesNotExist:
                pass
                # has_delegation = False

        # if group_by == 'component' or group_by == 'therapeutic_group':
        #     has_delegation = False

        # if not has_delegation:
        #     # if clues_id or by_delegation or delegation_id:
        #     if by_delegation:
        #         return Response(status=status.HTTP_400_BAD_REQUEST, data={
        #             'errors': 'No se puede desagregar la información por '
        #                       'delegación para este componente'
        #         })

        # base_class = DrugExport(request.data, by_delegation=by_delegation)
        base_class = DrugExport(request.data)
        drugs_data = base_class.build_spiral_data(group_by=group_by)
        data = {'drugs': list(drugs_data)}

        if display_totals:
            total_data = base_class.build_total_spiral_data(group_by=group_by)
            data['totals'] = list(total_data)

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False)
    def export(self, request):
        from task.aws.common import BotoUtils
        from django.utils import timezone

        report_name = "reporte.xlsx"
        drug_export = DrugExport(request.data)

        drugs_data = drug_export.build_worksheet_data("medicamentos")
        totals_data = drug_export.build_worksheet_data(
            "totales", is_total=True)

        boto_s3 = BotoUtils()
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        path_url = f"exports/drugs{now}.xlsx"

        excel_file = export_xlsx(
            report_name, [drugs_data, totals_data], in_memory=True)
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        boto_s3.save_file_in_aws(
            excel_file, path_url, content_type=content_type)
        return Response({
            "excel_file_url": boto_s3.get_full_path(path_url)
        }, status=status.HTTP_200_OK)
