from rds.models import Cluster
from rest_framework import serializers
from inai.api.serializers import MonthRecordSerializer


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'


class ClusterListSerializer(serializers.ModelSerializer):
    months_summary = serializers.SerializerMethodField()

    def get_months_summary(self, obj):
        from django.db.models import Count
        month_records = obj.month_records.all()\
            .values('stage_id', 'status_id', 'status__order', 'stage__order')\
            .annotate(total=Count('id'))\
            .order_by('stage__order', 'status__order')
        return month_records

    class Meta:
        model = Cluster
        fields = '__all__'


class ClusterFullSerializer(ClusterListSerializer):
    month_records = MonthRecordSerializer(many=True)
