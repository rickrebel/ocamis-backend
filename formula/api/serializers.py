from rest_framework import serializers

from formula.models import Drug, MotherDrugPriority


class MotherDrugPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = MotherDrugPriority
        fields = (
            'key',
        )


