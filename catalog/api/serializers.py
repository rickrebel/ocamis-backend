# -*- coding: utf-8 -*-
from rest_framework import serializers

from report.models import Responsable
from catalog.models import (
    State, Institution, CLUES, Alliances, Municipality, Disease, Entity
)
#from report.api.serializers import ResponsableListSerializer
from inai.models import MonthEntity


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
    institution = InstitutionSerializer(read_only=True)
    state = StateSimpleSerializer(read_only=True)
    clues = CLUESSerializer(read_only=True)

    class Meta:
        model = Entity
        fields = [
            "id", "institution", "state", "clues", "name", 
            "addl_params", "vigencia", "entity_type", "acronym",
            "notes", "is_pilot"]


class EntityFileControlsSerializer(serializers.ModelSerializer):
    file_controls = serializers.SerializerMethodField(read_only=True)
    
    def get_file_controls(self, obj):
        from inai.models import FileControl
        from inai.api.serializers import FileControlSemiFullSerializer
        queryset = FileControl.objects\
            .filter(petition_file_control__petition__entity=obj)\
            .distinct()\
            .prefetch_related(
                "data_group",
                "columns",
                "columns__column_transformations",
                #"petition_file_control",
                #"petition_file_control__data_files",
                #"petition_file_control__data_files__origin_file",
            )
        return FileControlSemiFullSerializer(queryset, many=True).data

    class Meta:
        model = Entity
        fields = ["file_controls"]


class EntityFullSerializer(EntitySerializer, EntityFileControlsSerializer):
#class EntityFullSerializer(EntitySerializer):
    from inai.api.serializers import (
        PetitionSemiFullSerializer, MonthEntitySimpleSerializer)

    petitions = PetitionSemiFullSerializer(many=True)
    months = MonthEntitySimpleSerializer(many=True)
    #entity_type = read_only_fields(many=True)

    class Meta:
        model = Entity
        fields = "__all__"


class EntityVizSerializer(EntitySerializer):
    #from inai.api.serializers import MonthEntitySimpleSerializer
    from inai.api.serializers_viz import (
        PetitionVizSerializer, MonthEntityVizSerializer)

    entity_type = serializers.ReadOnlyField()
    petitions = PetitionVizSerializer(many=True)
    months = MonthEntityVizSerializer(many=True, read_only=True)
    #months = serializers.SerializerMethodField(read_only=True)

    #def get_months(self, obj):
    #    return MonthEntity.objects.filter(entity=obj)\
    #        .values_list("year_month", flat=True).distinct()


    class Meta:
        model = Entity
        fields = [
            "id",
            "name",
            "acronym",
            "is_pilot",
            "institution",
            "state",
            "clues",
            "entity_type",
            "petitions",
            "months",
            "population",
        ]
