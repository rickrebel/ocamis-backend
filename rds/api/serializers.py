from rds.models import Cluster
from rest_framework import serializers


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'
