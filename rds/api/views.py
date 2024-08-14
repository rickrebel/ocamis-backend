from . import serializers
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from task.builder import TaskBuilder

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerListRetrieveMix as ListRetrieveMix)

from rds.models import Cluster


class ClusterViewSet(ListRetrieveUpdateMix):
    queryset = Cluster.objects.all()
    serializer_class = serializers.ClusterListSerializer
    permission_classes = [permissions.IsAuthenticated]

    action_serializers = {
        'retrieve': serializers.ClusterFullSerializer,
        'list': serializers.ClusterListSerializer,
        'update': serializers.ClusterSerializer,
        'send_clusters': serializers.ClusterSerializer,
    }

    @action(methods=["post"], detail=True)
    def send_clusters(self, request, *args, **kwargs):
        from classify_task.models import Stage
        from rds.misc_mixins.cluster_mix import ClusterMix
        print("send_clusters")
        stage_name = request.data.get('stage', None)
        cluster = self.get_object()

        months_not_inserted = cluster.month_records\
            .exclude(stage_id='insert', status_id='finished')
        if months_not_inserted.exists():
            return Response(
                {"errors": ["Para enviar los clusters a la siguiente etapa, "
                            "todos los meses deben estar insertados"]},
                status=status.HTTP_400_BAD_REQUEST)

        stage = Stage.objects.get(name=stage_name)
        function_name = stage.main_function.name
        function_finished = stage.finished_function
        base_task = TaskBuilder(
            function_name, models=[cluster], request=request,
            finished_function=function_finished)
        cluster_mix = ClusterMix(cluster, base_task)
        getattr(cluster_mix, function_name)()

        return Response(status=status.HTTP_200_OK)






