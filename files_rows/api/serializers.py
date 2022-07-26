# -*- coding: utf-8 -*-
from rest_framework import serializers

from files_rows.models import (
    GroupFile, Petition, PetitionGroupFile, Transformation,
    DataFile, MonthEntity, PetitionMonth, ProcessFile, NameColumn)

from files_categories.api.serializers import (
    TypeFileSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer)
from parameter.api.serializers import (
    CleanFunctionSimpleSerializer, GroupDataSimpleSerializer,
    TypeDataSimpleSerializer, FinalFieldSimpleSerializer)



class GroupFileSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupFile
        fields = "__all__"


class ProcessFileSerializer(serializers.ModelSerializer):
    type_file = TypeFileSimpleSerializer()

    class Meta:
        model = ProcessFile
        fields = "__all__"


class TransformationSerializer(serializers.ModelSerializer):
    clean_function = CleanFunctionSimpleSerializer()

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnSerializer(serializers.ModelSerializer):
    type_data = TypeDataSimpleSerializer()
    column_type = ColumnTypeSimpleSerializer()
    tranformations = TransformationSerializer(
        many=True, source="column_tranformations")
    final_field = FinalFieldSimpleSerializer()

    class Meta:
        model = NameColumn
        fields = "__all__"


class GroupFileSerializer(serializers.ModelSerializer):
    group_data = GroupDataSimpleSerializer()
    type_file = TypeFileSimpleSerializer()
    status_register = StatusControlSimpleSerializer()
    tranformations = TransformationSerializer(
        many=True, source="group_tranformations")

    class Meta:
        model = GroupFile
        fields = "__all__"


class GroupFileFullSerializer(GroupFileSerializer):
    columns = NameColumnSerializer(many=True)

    class Meta:
        model = GroupFile
        fields = "__all__"


class MonthEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = "__all__"


class MonthEntitySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = ["year_month"]


class DataFileSerializer(serializers.ModelSerializer):
    month_entity = MonthEntitySimpleSerializer()
    status_process = StatusControlSimpleSerializer()

    class Meta:
        model = DataFile
        fields = "__all__"


class PetitionMonthSerializer(serializers.ModelSerializer):
    month_entity = MonthEntitySimpleSerializer()

    class Meta:
        model = PetitionMonth
        fields = "__all__"


class PetitionGroupFileSerializer(serializers.ModelSerializer):
    group_file = GroupFileSerializer()
    data_files = DataFileSerializer(many=True)

    class Meta:
        model = PetitionGroupFile
        fields = "__all__"


class PetitionFullSerializer(serializers.ModelSerializer):
    file_groups = PetitionGroupFileSerializer(many=True)
    petition_months = PetitionMonthSerializer(many=True)
    process_files = ProcessFileSerializer(many=True)

    class Meta:
        model = Petition
        fields = ["id", "date_send"]
