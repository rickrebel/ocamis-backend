from rest_framework import serializers

from data_param.api.serializers import FileControlSerializer, NameColumnSerializer
from inai.models import (
    Petition, PetitionFileControl, MonthRecord, RequestTemplate, Variable,
    PetitionBreak, PetitionNegativeReason, WeekRecord, Complaint)
from respond.api.serializers import (
    ReplyFileSerializer, DataFileSerializer, DataFileSimpleSerializer)
from respond.models import TableFile
from data_param.models import Transformation, NameColumn, FileControl

from category.api.serializers import (
    NegativeReasonSimpleSerializer)


class TransformationEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = NameColumn
        fields = "__all__"


class MonthRecordSerializer(serializers.ModelSerializer):
    # all_laps_inserted = serializers.SerializerMethodField(read_only=True)
    # def get_all_laps_inserted(self, obj):
    #     return obj.laps.filter(lap=0).first().all_laps_inserted

    class Meta:
        model = MonthRecord
        fields = [
            "id", "year_month", "human_name", "rx_count", "drugs_count",
            "duplicates_count", "shared_count", "last_transformation",
            "last_crossing", "last_merge", "last_pre_insertion",
            "cluster",
            "error_process", "last_indexing", "last_behavior",
            "last_insertion", "stage", "status", "provider_id", ]


class MonthRecordFullSerializer(serializers.ModelSerializer):
    drugs_counts = serializers.SerializerMethodField(read_only=True)
    behavior_counts = serializers.SerializerMethodField(read_only=True)

    def get_drugs_counts(self, obj):
        from geo.api.serializers import calc_drugs_summarize
        table_files = TableFile.objects.filter(
            week_record__month_record=obj)
        # print("calc_drugs_summarize \n", calc_drugs_summarize(obj, table_files))
        if table_files:
            drugs_sum = calc_drugs_summarize(obj, table_files)
            return drugs_sum.get(str(obj.id), {})
        return {}
        # print("drugs_sum", drugs_sum)
        # return drugs_sum

    def get_behavior_counts(self, obj):
        from geo.api.serializers import calc_sheet_files_summarize
        return calc_sheet_files_summarize(month_records=[obj])

    class Meta:
        model = MonthRecord
        fields = [
            "id", "year_month", "human_name", "rx_count", "drugs_count",
            "duplicates_count", "shared_count", "last_transformation",
            "last_crossing", "last_merge", "last_pre_insertion",
            "cluster",
            "error_process", "last_indexing", "last_behavior",
            "last_insertion", "stage", "status", "provider_id",
            "behavior_counts", "drugs_counts"]


class MonthRecordSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthRecord
        fields = ["id", "year_month", "human_name", "provider"]


class WeekRecordSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeekRecord
        exclude = [
            "rx_count", "duplicates_count", "shared_count",
            "last_transformation", "last_crossing", "last_behavior"]


class PetitionFileControlCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        read_only_fields = ["data_files"]


class PetitionFileControlSerializer(serializers.ModelSerializer):
    data_files = serializers.SerializerMethodField(read_only=True)

    def get_data_files(self, obj):
        return []

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        # read_only_fields = ["file_control", "petition"]


class PetitionFileControlFullSerializer(PetitionFileControlSerializer):
    # file_control = FileControlSimpleSerializer()
    # data_files = DataFileSerializer(many=True)
    data_files = serializers.SerializerMethodField(read_only=True)

    def get_data_files(self, obj):
        return DataFileSerializer(obj.data_files.all(), many=True).data

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        ordering = ["file_control_id"]


class FileControlFullSerializer(FileControlSerializer):
    petition_file_control = PetitionFileControlSerializer(
        many=True, read_only=True)
    columns = NameColumnSerializer(many=True)
    real_columns = serializers.IntegerField(read_only=True)

    class Meta:
        model = FileControl
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
        # write_only_fields = ('date_break_id',)


class PetitionNegativeReasonSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetitionNegativeReason
        fields = "__all__"


class PetitionNegativeReasonSerializer(PetitionNegativeReasonSimpleSerializer):
    negative_reason = NegativeReasonSimpleSerializer()


class PetitionSmallSerializer(serializers.ModelSerializer):
    # month_records = MonthRecordSimpleSerializer(many=True)
    last_year_month = serializers.CharField(read_only=True)
    first_year_month = serializers.CharField(read_only=True)
    months_in_description = serializers.CharField(read_only=True)

    class Meta:
        model = Petition
        fields = "__all__"


class DataFileCountSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        return value.count()


class ComplaintSerializer(serializers.ModelSerializer):

    class Meta:
        model = Complaint
        fields = "__all__"


class PetitionSemiFullSerializer(PetitionSmallSerializer):
    petition_file_controls = PetitionFileControlSerializer(
        many=True, source="file_controls")
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)
    break_dates = PetitionBreakSerializer(many=True)
    reply_files = ReplyFileSerializer(many=True)
    complaints = ComplaintSerializer(many=True)
    # reply_files = serializers.SerializerMethodField(read_only=True)

    def get_reply_files(self, obj):
        return []


class PetitionFullSerializer(PetitionSemiFullSerializer):
    petition_file_controls = PetitionFileControlFullSerializer(
        many=True, source="file_controls")


class PetitionEditSerializer(serializers.ModelSerializer):
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)
    # folio_petition = serializers.CharField(required=False)
    # status_data = StatusControlSimpleSerializer(read_only=True)
    # status_data_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="old_status_data",
    #     queryset=StatusControl.objects.all(), required=False)

    class Meta:
        model = Petition
        read_only_fields = ["id", "break_dates", "month_records"]
        fields = "__all__"


class VariableSerializer(serializers.ModelSerializer):

    class Meta:
        model = Variable
        fields = "__all__"


class RequestTemplateSerializer(serializers.ModelSerializer):
    variables = VariableSerializer(many=True, read_only=True)

    class Meta:
        model = RequestTemplate
        fields = "__all__"


