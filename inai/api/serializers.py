# -*- coding: utf-8 -*-
from rest_framework import serializers

from inai.models import (
    FileControl, Petition, PetitionFileControl, Transformation,
    DataFile, MonthEntity, PetitionMonth, ProcessFile, NameColumn,
    PetitionBreak, PetitionNegativeReason)

from category.models import StatusControl, FileType

from category.api.serializers import (
    NegativeReasonSimpleSerializer)

from catalog.api.serializers import EntitySerializer

from data_param.api.serializers import (
    CleanFunctionSimpleSerializer, DataGroupSimpleSerializer,
    DataTypeSimpleSerializer, FinalFieldSimpleSerializer)


class ProcessFileSerializer(serializers.ModelSerializer):
    #name = serializers.ReadOnlyField(source="file.name", required=False)
    #url = serializers.ReadOnlyField(source="file.url", required=False)
    """file_type = FileTypeSimpleSerializer(read_only=True)
    file_type_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="file_type",
        queryset=FileType.objects.all())"""
    name = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        return obj.file.name if obj.file else None
    def get_url(self, obj):
        return obj.file.url if obj.file else None

    class Meta:
        model = ProcessFile
        fields = "__all__"
        read_only_fields = ["petition"]


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
    #clean_function = CleanFunctionSimpleSerializer()

    class Meta:
        model = Transformation
        fields = "__all__"


class TransformationEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnSerializer(serializers.ModelSerializer):
    #data_type = DataTypeSimpleSerializer()
    #column_type = ColumnTypeSimpleSerializer()
    transformations = TransformationSerializer(
        many=True, source="column_transformations")
    #final_field = FinalFieldSimpleSerializer()

    class Meta:
        model = NameColumn
        fields = "__all__"


class NameColumnEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = NameColumn
        fields = "__all__"


class MonthEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = "__all__"


class MonthEntitySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthEntity
        fields = ["year_month", "human_name"]


class DataFileSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = DataFile
        fields = ["id", "name", "url"]


class DataFileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    origin_file = DataFileSimpleSerializer(read_only=True)
    """month_entity = MonthEntitySimpleSerializer(read_only=True)
    status_process = StatusControlSimpleSerializer(read_only=True)
    month_entity_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="month_entity",
        queryset=MonthEntity.objects.all(), required=False)
    status_process_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_process",
        queryset=StatusControl.objects.all()) """
    origin_file_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="origin_file",
        queryset=DataFile.objects.all(), required=False)
    petition_file_control_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="petition_file_control",
        queryset=PetitionFileControl.objects.all())


    class Meta:
        model = DataFile
        fields = "__all__"
        read_only_fields = ["petition_file_control"]


class DataFileEditSerializer(DataFileSerializer):

    class Meta:
        model = DataFile
        fields = "__all__"
        read_only_fields = ["petition_file_control", "file"]


class DataFileSerializer2(serializers.ModelSerializer):
    month_entity = MonthEntitySimpleSerializer()
    #status_process = StatusControlSimpleSerializer()

    class Meta:
        model = DataFile
        fields = "__all__"


class PetitionMonthSerializer(serializers.ModelSerializer):
    month_entity = MonthEntitySimpleSerializer(read_only=True)

    class Meta:
        model = PetitionMonth
        fields = "__all__"


class PetitionMiniSerializer(serializers.ModelSerializer):
    petition_months = PetitionMonthSerializer(many=True)
    entity = serializers.SerializerMethodField(read_only=True)
    last_year_month = serializers.CharField(read_only=True)
    first_year_month = serializers.CharField(read_only=True)    

    def get_entity(self, obj):
        show_inst = self.context.get("show_institution", False)
        request = self.context.get("request", False)
        if request and request.method == "GET" and show_inst:
            return EntitySerializer(obj.entity).data
        return obj.entity.id

    class Meta:
        model = Petition
        fields = "__all__"


class PetitionFileControlSerializer(serializers.ModelSerializer):
    #file_control = FileControlSerializer()
    data_files = DataFileSerializer(many=True, read_only=True)
    petition = PetitionMiniSerializer(read_only=True)
    petition_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="petition",
        queryset=Petition.objects.all())
    file_control_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="file_control",
        queryset=FileControl.objects.all())

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        read_only_fields = ["file_control"]


class FileControlSimpleSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer(read_only=True)
    #file_type = FileTypeSimpleSerializer(read_only=True)
    #status_register = StatusControlSimpleSerializer(read_only=True)

    class Meta:
        model = FileControl
        fields = "__all__"


class FileControlSerializer(FileControlSimpleSerializer):
    from category.models import FileType
    from data_param.models import DataGroup
    petition_file_control = PetitionFileControlSerializer(
        many=True, read_only=True)
    transformations = TransformationSerializer(
        many=True, source="file_transformations", read_only=True)
    data_group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="data_group",
        queryset=DataGroup.objects.all(), required=False)
    """file_type_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="file_type",
        queryset=FileType.objects.all())
    status_register_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_register",
        queryset=StatusControl.objects.all())"""


class FileControlFullSerializer(FileControlSerializer):
    columns = NameColumnSerializer(many=True)

    class Meta:
        model = FileControl
        fields = "__all__"


class PetitionFileControlFullSerializer(PetitionFileControlSerializer):
    file_control = FileControlSimpleSerializer()
    data_files = DataFileSerializer(many=True)

    class Meta:
        model = PetitionFileControl
        fields = "__all__"


class PetitionFileControlDeepSerializer(PetitionFileControlSerializer):
    file_control = FileControlFullSerializer()
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


class PetitionNegativeReasonSerializer(FileControlSerializer):
    negative_reason = NegativeReasonSimpleSerializer()

    class Meta:
        model = PetitionNegativeReason
        fields = "__all__"


class PetitionSmallSerializer(serializers.ModelSerializer):
    petition_months = PetitionMonthSerializer(many=True)
    process_files = ProcessFileSerializer(many=True)
    last_year_month = serializers.CharField(read_only=True)
    first_year_month = serializers.CharField(read_only=True)
    months_in_description = serializers.CharField(read_only=True)

    class Meta:
        model = Petition
        fields = "__all__"


class PetitionFullSerializer(PetitionSmallSerializer):
    petition_file_controls = PetitionFileControlFullSerializer(
        many=True, source="file_controls")
    break_dates = PetitionBreakSerializer(many=True)
    #status_data = StatusControlSimpleSerializer()
    #status_petition = StatusControlSimpleSerializer()
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)


class PetitionEditSerializer(serializers.ModelSerializer):
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)
    """status_data = StatusControlSimpleSerializer(read_only=True)
    status_data_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_data",
        queryset=StatusControl.objects.all(), required=False)
    status_petition = StatusControlSimpleSerializer(
        read_only=True)
    status_complain = StatusControlSimpleSerializer(
        read_only=True)
    status_petition_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_petition",
        queryset=StatusControl.objects.all(), required=False)
    status_complain_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="status_complain",
        queryset=StatusControl.objects.all(), required=False)"""

    class Meta:
        model = Petition
        read_only_fields = ["id", "break_dates"]
        fields = "__all__"
