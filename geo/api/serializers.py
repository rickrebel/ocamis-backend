# -*- coding: utf-8 -*-
from rest_framework import serializers

from report.models import Responsable
from geo.models import (
    State, Institution, CLUES, Alliances, Municipality, Disease, Agency
)
#from report.api.serializers import ResponsableListSerializer
from inai.models import MonthAgency


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


class AgencySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    state = StateSimpleSerializer(read_only=True)
    clues = CLUESSerializer(read_only=True)

    class Meta:
        model = Agency
        fields = [
            "id", "institution", "state", "clues", "name", 
            "addl_params", "vigencia", "agency_type", "acronym",
            "notes", "is_pilot"]


class AgencyFileControlsSerializer(serializers.ModelSerializer):
    file_controls = serializers.SerializerMethodField(read_only=True)
    
    def get_file_controls(self, obj):
        from data_param.models import FileControl
        from data_param.api.serializers import FileControlSemiFullSerializer
        queryset = FileControl.objects\
            .filter(agency=obj)\
            .distinct()\
            .order_by("data_group", "id")\
            .prefetch_related(
                "data_group",
                "columns",
                "columns__column_transformations",
            )
        return FileControlSemiFullSerializer(queryset, many=True).data

    class Meta:
        model = Agency
        fields = ["file_controls"]


# from inai.api.serializers import SheetFileSimpleSerializer
# return SheetFileSimpleSerializer(queryset, many=True).data
# queryset = SheetFile.objects\
#     .filter(data_file__entity=obj.entity)\
#     .order_by("year_month")
# class AgencyFullSerializer(AgencySerializer):
class AgencyFullSerializer(AgencySerializer, AgencyFileControlsSerializer):
    from inai.api.serializers import (
        PetitionSemiFullSerializer, MonthEntitySerializer)

    petitions = PetitionSemiFullSerializer(many=True)
    #agency_type = read_only_fields(many=True)
    # months = MonthEntitySimpleSerializer(many=True)
    months = MonthEntitySerializer(many=True)
    # sheet_files = serializers.SerializerMethodField(read_only=True)
    #
    # def get_sheet_files(self, obj):
    #     from inai.models import SheetFile
    #     from django.db.models import Sum
    #     result = SheetFile.objects\
    #         .filter(data_file__entity=obj.entity)\
    #         .values("year_month")\
    #         .annotate(
    #             prescriptions_count=Sum("prescriptions_count"),
    #             duplicates_count=Sum("duplicates_count"),
    #             shared_count=Sum("shared_count"),
    #         )\
    #         .order_by("year_month")
    #     return result

    class Meta:
        model = Agency
        fields = "__all__"


class AgencyVizSerializer(AgencySerializer):
    #from inai.api.serializers import MonthEntitySimpleSerializer
    from inai.api.serializers_viz import (
        PetitionVizSerializer, MonthEntityVizSerializer)

    agency_type = serializers.ReadOnlyField()
    petitions = PetitionVizSerializer(many=True)
    months = MonthEntityVizSerializer(many=True, read_only=True)
    #months = serializers.SerializerMethodField(read_only=True)

    #def get_months(self, obj):
    #    return MonthAgency.objects.filter(agency=obj)\
    #        .values_list("year_month", flat=True).distinct()

    class Meta:
        model = Agency
        fields = [
            "id",
            "name",
            "acronym",
            "is_pilot",
            "institution",
            "state",
            "clues",
            "agency_type",
            "petitions",
            "months",
            "population",
        ]
