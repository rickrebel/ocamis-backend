# -*- coding: utf-8 -*-
from rest_framework import serializers

from report.models import Responsable
from catalog.models import (
    State, Institution, CLUES, Alliances, Municipality, Disease, Entity
)
#from report.api.serializers import ResponsableListSerializer


class ResponsableListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Responsable
        fields = "__all__"


class MunicipalityListSerializers(serializers.ModelSerializer):

    class Meta:
        model = Municipality
        fields = "__all__"


class StateSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = "__all__"


class StateSerializer(serializers.ModelSerializer):
    municipalities = MunicipalityListSerializers(many=True)

    class Meta:
        model = State
        fields = "__all__"


class StateListSerializer(serializers.ModelSerializer):
    responsables = ResponsableListSerializer(many=True)

    class Meta:
        model = State
        fields = "__all__"
        read_only_fields = ["responsables"]


class InstitutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Institution
        fields = "__all__"


class InstitutionListSerializer(serializers.ModelSerializer):
    responsables = ResponsableListSerializer(many=True)

    class Meta:
        model = Institution
        fields = "__all__"
        read_only_fields = ["responsables"]


class CLUESSerializer(serializers.ModelSerializer):

    class Meta:
        model = CLUES
        fields = ['id', 'name', 'real_name', 'alter_clasifs',
                  'prev_clasif_name', 'clasif_name', 'number_unity',
                  'total_unities', 'municipality']


class CLUESListSerializer(serializers.ModelSerializer):
    responsables = ResponsableListSerializer(many=True)

    class Meta:
        model = CLUES
        fields = ['id', 'name', 'real_name', 'alter_clasifs',
                  'prev_clasif_name', 'clasif_name', 'number_unity',
                  'total_unities', 'municipality', "responsables"]
        read_only_fields = ["responsables"]


class CLUESFullSerializer(serializers.ModelSerializer):

    class Meta:
        model = CLUES
        fields = "__all__"
        depth = 1


class AlliancesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alliances
        fields = "__all__"


class DiseaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Disease
        fields = "__all__"


class EntitySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer()
    state = StateSimpleSerializer()
    clues = CLUESSerializer()

    class Meta:
        model = Entity
        fields = [
            "id", "institution", "state", "clues", "name", 
            "addl_params", "vigencia", "entity_type", "acronym"]


class EntityFullSerializer(EntitySerializer):
    from inai.api.serializers import (
        PetitionFullSerializer, MonthEntitySimpleSerializer)
    petitions = PetitionFullSerializer(many=True)
    months = MonthEntitySimpleSerializer(many=True)
    #entity_type = read_only_fields(many=True)
    entity_type = serializers.ReadOnlyField()

    class Meta:
        model = Entity
        fields = "__all__"
