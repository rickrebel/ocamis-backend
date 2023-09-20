from rest_framework import serializers

from mat.models import MotherDrugPriority, MotherDrug


class MotherDrugPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = MotherDrugPriority
        fields = (
            'key',
        )


class MotherDrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotherDrug
        fields = (
            'key',
        )
