# -*- coding: utf-8 -*-
from rest_framework import serializers

from inai.models import (
    FileControl, Petition, PetitionFileControl, Transformation,
    DataFile, MonthEntity, PetitionMonth, ProcessFile, NameColumn,
    PetitionBreak)

from category.models import StatusControl

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


class ProcessFileEditSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = ProcessFile
        fields = "__all__"
        read_only_fields = ["petition"]


class AscertainableSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = ProcessFile
        fields = ["id", "name", "url"]


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
    #file_control = FileControlSerializer()
    data_files = DataFileSerializer(many=True)

    class Meta:
        model = PetitionFileControl
        fields = "__all__"


class PetitionBreakSerializer(serializers.ModelSerializer):
    from category.api.serializers import DateBreakSimpleSerializer
    from category.models import DateBreak
    date_break = DateBreakSimpleSerializer(read_only=True)
    date_break_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="date_break",
        queryset=DateBreak.objects.all())

    class Meta:
        model = PetitionBreak
        fields = "__all__"
        read_only_fields = ["petition"]
        #write_only_fields = ('date_break_id',)


class PetitionSmallSerializer(serializers.ModelSerializer):
    petition_months = PetitionMonthSerializer(many=True)
    process_files = ProcessFileSerializer(many=True)
    last_year_month = serializers.CharField(read_only=True)

    class Meta:
        model = Petition
        fields = "__all__"


class PetitionFullSerializer(PetitionSmallSerializer):
    file_controls = PetitionFileControlSerializer(many=True)
    break_dates = PetitionBreakSerializer(many=True)
    status_data = StatusControlSimpleSerializer()
    status_petition = StatusControlSimpleSerializer()


class PetitionEditSerializer(serializers.ModelSerializer):
    status_data = StatusControlSimpleSerializer(read_only=True)
    status_data_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_data",
        queryset=StatusControl.objects.all())
    status_petition = StatusControlSimpleSerializer(read_only=True)
    status_petition_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_petition",
        queryset=StatusControl.objects.all())

    class Meta:
        model = Petition
        read_only_fields = ["id", "break_dates"]
        fields = "__all__"

