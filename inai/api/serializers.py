# -*- coding: utf-8 -*-
from rest_framework import serializers

from inai.models import (
    FileControl, Petition, PetitionFileControl, Transformation,
    DataFile, MonthEntity, PetitionMonth, ProcessFile, NameColumn)

from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer,
    ColumnTypeSimpleSerializer)

from data_param.api.serializers import (
    CleanFunctionSimpleSerializer, DataGroupSimpleSerializer,
    DataTypeSimpleSerializer, FinalFieldSimpleSerializer)


class FileControlSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileControl
        fields = "__all__"


class ProcessFileSerializer(serializers.ModelSerializer):
    file_type = FileTypeSimpleSerializer()

    class Meta:
        model = ProcessFile
        fields = "__all__"


class TransformationSerializer(serializers.ModelSerializer):
    clean_function = CleanFunctionSimpleSerializer()

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnSerializer(serializers.ModelSerializer):
    data_type = DataTypeSimpleSerializer()
    column_type = ColumnTypeSimpleSerializer()
    tranformations = TransformationSerializer(
        many=True, source="column_tranformations")
    final_field = FinalFieldSimpleSerializer()

    class Meta:
        model = NameColumn
        fields = "__all__"


class FileControlSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer()
    file_type = FileTypeSimpleSerializer()
    status_register = StatusControlSimpleSerializer()
    tranformations = TransformationSerializer(
        many=True, source="file_tranformations")

    class Meta:
        model = FileControl
        fields = "__all__"


class FileControlFullSerializer(FileControlSerializer):
    columns = NameColumnSerializer(many=True)

    class Meta:
        model = FileControl
        fields = "__all__"


class MonthEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = "__all__"


class MonthEntitySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = ["year_month", "human_name"]


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


class PetitionFileControlSerializer(serializers.ModelSerializer):
    file_control = FileControlSerializer()
    data_files = DataFileSerializer(many=True)

    class Meta:
        model = PetitionFileControl
        fields = "__all__"


class PetitionFullSerializer(serializers.ModelSerializer):
    file_control = PetitionFileControlSerializer(many=True)
    petition_months = PetitionMonthSerializer(many=True)
    process_files = ProcessFileSerializer(many=True)
    #break_dates = BreakDateSerializer(many=True)

    class Meta:
        model = Petition
        #fields = ["id", "date_send"]
        fields = "__all__"
