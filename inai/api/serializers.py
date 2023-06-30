from rest_framework import serializers

from data_param.api.serializers import FileControlSerializer, NameColumnSerializer
from inai.models import (
    Petition, PetitionFileControl, DataFile, EntityMonth,
    ReplyFile, PetitionBreak, PetitionNegativeReason, SheetFile, LapSheet,
    TableFile, CrossingSheet, Behavior, EntityWeek)
from data_param.models import Transformation, NameColumn, FileControl

from category.api.serializers import (
    NegativeReasonSimpleSerializer)


class ReplyFileSerializer(serializers.ModelSerializer):
    # name = serializers.ReadOnlyField(source="file.name", required=False)
    # url = serializers.ReadOnlyField(source="file.url", required=False)
    name = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)
    real_name = serializers.SerializerMethodField(read_only=True)
    short_name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        return obj.file.name if obj.file else None

    def get_url(self, obj):
        return obj.file.url if obj.file else None

    def get_real_name(self, obj):
        return obj.file.name.split("/")[-1]

    def get_short_name(self, obj):
        real_name = obj.file.name.split("/")[-1]
        return f"{real_name[:25]}...{real_name[-15:]}" \
            if len(real_name) > 42 else real_name

    class Meta:
        model = ReplyFile
        fields = "__all__"
        read_only_fields = ["petition"]


class ReplyFileEditSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = ReplyFile
        fields = "__all__"
        read_only_fields = ["petition"]


class AscertainableSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = ReplyFile
        fields = ["id", "name", "url"]


class TransformationEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = NameColumn
        fields = "__all__"


class EntityMonthSerializer(serializers.ModelSerializer):
    # all_laps_inserted = serializers.SerializerMethodField(read_only=True)

    # def get_all_laps_inserted(self, obj):
    #     return obj.laps.filter(lap=0).first().all_laps_inserted

    class Meta:
        model = EntityMonth
        fields = [
            "id", "year_month", "human_name", "rx_count",
            "duplicates_count", "shared_count", "last_transformation",
            "last_crossing", "last_insertion"]


class TableFileSerializer(serializers.ModelSerializer):
    # name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = TableFile
        fields = ["id", "url", "collection"]


class TableFileAwsSerializer(serializers.ModelSerializer):
    file = serializers.ReadOnlyField(source="file.name")
    # sheet_behavior = serializers.CharField(
    #     source="lap_sheet.sheet_file.behavior_id")
    sheet_behavior = serializers.SerializerMethodField(read_only=True)

    def get_sheet_behavior(self, obj):
        if obj.lap_sheet:
            return obj.lap_sheet.sheet_file.behavior_id
        return None

    class Meta:
        model = TableFile
        fields = [
            "id", "file", "collection", "year", "month", "year_month",
            "sheet_behavior", "iso_week", "iso_year", "year_week"]
        # "iso_year", "iso_week", "delegation_name"]


class LapSheetSerializer(serializers.ModelSerializer):

    class Meta:
        model = LapSheet
        fields = "__all__"


class LapSheetFullSerializer(serializers.ModelSerializer):
    table_files = TableFileSerializer(read_only=True, many=True)

    class Meta:
        model = LapSheet
        fields = "__all__"


class SheetFileSerializer(serializers.ModelSerializer):
    # name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    laps = LapSheetFullSerializer(read_only=True, many=True)

    class Meta:
        model = SheetFile
        fields = "__all__"


class SheetFileSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = SheetFile
        # fields = "__all__"
        exclude = ["sample_data", "error_process", "warnings"]


class SheetFileMonthSerializer(SheetFileSimpleSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    table_sums = serializers.SerializerMethodField(read_only=True)

    def get_table_sums(self, obj):
        from django.db.models import Sum, F
        sum_fields = ["drugs_count", "rx_count", "duplicates_count", "shared_count"]
        if obj.rx_count:
            final_sums = {field: getattr(obj, field) for field in sum_fields}
            return final_sums
        query_sums = [Sum(field) for field in sum_fields]
        # query_annotations = {field: Sum(field) for field in sum_fields}
        last_lap = obj.laps.filter(lap=0).first()
        result_sums = last_lap.table_files.filter(
            collection__isnull=True).aggregate(*query_sums)
        result_with_init_names = {
            field: result_sums[f"{field}__sum"] for field in sum_fields}
        return result_with_init_names

    class Meta:
        model = SheetFile
        # fields = "__all__"
        exclude = ["sample_data", "error_process", "warnings"]


class SheetFileEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = SheetFile
        fields = "__all__"
        read_only_fields = ["file", "sheet_name", "data_file", "file_type"]


class CrossingSheetSimpleSerializer(serializers.ModelSerializer):
    # name = serializers.ReadOnlyField(source="file.name")

    class Meta:
        model = CrossingSheet
        fields = "__all__"


class DataFileSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = DataFile
        fields = ["id", "name", "url"]


class DataFileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    #origin_file = DataFileSimpleSerializer(read_only=True)
    # origin_file_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="origin_file",
    #     queryset=DataFile.objects.all(), required=False)
    # petition_file_control_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="petition_file_control",
    #     queryset=PetitionFileControl.objects.all())
    # child_files = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    has_sample_data = serializers.SerializerMethodField(read_only=True)
    short_name = serializers.SerializerMethodField(read_only=True)
    real_name = serializers.SerializerMethodField(read_only=True)
    petition = serializers.IntegerField(
        source="petition_file_control.petition_id", read_only=True)

    def get_has_sample_data(self, obj):
        # return bool(obj.sample_data)
        return bool(obj.sheet_files.exists())

    def get_real_name(self, obj):
        return obj.file.name.split("/")[-1]

    def get_short_name(self, obj):
        real_name = obj.file.name.split("/")[-1]
        return f"{real_name[:25]}...{real_name[-15:]}" \
            if len(real_name) > 42 else real_name

    class Meta:
        model = DataFile
        read_only_fields = ["has_sample_data"]
        exclude = ('sample_data', )


class DataFileEditSerializer(DataFileSerializer):

    class Meta:
        model = DataFile
        # fields = "__all__"
        exclude = ('sample_data',)
        read_only_fields = ["petition_file_control", "file"]


class DataFileFullSerializer(DataFileSerializer):
    sheet_files = SheetFileSerializer(many=True, read_only=True)

    class Meta:
        model = DataFile
        exclude = ('sample_data',)
        read_only_fields = ["petition_file_control", "file"]


class EntityMonthSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = EntityMonth
        fields = ["year_month", "human_name"]


class EntityWeekSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = EntityWeek
        exclude = [
            "rx_count", "duplicates_count", "shared_count",
            "last_transformation", "last_crossing"]


# class PetitionMonthSerializer(serializers.ModelSerializer):
#     entity_month = EntityMonthSimpleSerializer(read_only=True)
#
#     class Meta:
#         model = PetitionMonth
#         fields = "__all__"


# class PetitionMiniSerializer(serializers.ModelSerializer):
#     petition_months = PetitionMonthSerializer(many=True)
#     #agency = serializers.SerializerMethodField(read_only=True)
#     last_year_month = serializers.CharField(read_only=True)
#     first_year_month = serializers.CharField(read_only=True)
#
#     def get_agency(self, obj):
#         show_inst = self.context.get("show_institution", False)
#         request = self.context.get("request", False)
#         if request and request.method == "GET" and show_inst:
#             return AgencySerializer(obj.agency).data
#         return obj.agency.id
#
#     class Meta:
#         model = Petition
#         fields = "__all__"


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
        #read_only_fields = ["file_control", "petition"]


class PetitionFileControlFullSerializer(PetitionFileControlSerializer):
    # file_control = FileControlSimpleSerializer()
    # data_files = DataFileSerializer(many=True)
    data_files = serializers.SerializerMethodField(read_only=True)

    def get_data_files(self, obj):
        return DataFileSerializer(obj.data_files.all(), many=True).data

    class Meta:
        model = PetitionFileControl
        fields = "__all__"


class FileControlFullSerializer(FileControlSerializer):
    petition_file_control = PetitionFileControlSerializer(
        many=True, read_only=True)
    columns = NameColumnSerializer(many=True)

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
        #write_only_fields = ('date_break_id',)


class PetitionNegativeReasonSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetitionNegativeReason
        fields = "__all__"


class PetitionNegativeReasonSerializer(PetitionNegativeReasonSimpleSerializer):
    negative_reason = NegativeReasonSimpleSerializer()


class PetitionSmallSerializer(serializers.ModelSerializer):
    # petition_months = PetitionMonthSerializer(many=True)
    entity_months = EntityMonthSimpleSerializer(many=True)
    last_year_month = serializers.CharField(read_only=True)
    first_year_month = serializers.CharField(read_only=True)
    months_in_description = serializers.CharField(read_only=True)

    class Meta:
        model = Petition
        fields = "__all__"


class PetitionSemiFullSerializer(PetitionSmallSerializer):
    petition_file_controls = PetitionFileControlSerializer(
        many=True, source="file_controls")
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)
    break_dates = PetitionBreakSerializer(many=True)


class PetitionFullSerializer(PetitionSemiFullSerializer):
    reply_files = ReplyFileSerializer(many=True)
    petition_file_controls = PetitionFileControlFullSerializer(
        many=True, source="file_controls")


class PetitionEditSerializer(serializers.ModelSerializer):
    negative_reasons = PetitionNegativeReasonSerializer(
        many=True, read_only=True)
    # status_data = StatusControlSimpleSerializer(read_only=True)
    # status_data_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="status_data",
    #     queryset=StatusControl.objects.all(), required=False)
    # status_petition = StatusControlSimpleSerializer(
    #     read_only=True)
    # status_complain = StatusControlSimpleSerializer(
    #     read_only=True)
    # status_petition_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="status_petition",
    #     queryset=StatusControl.objects.all(), required=False)
    # status_complain_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="status_complain",
    #     queryset=StatusControl.objects.all(), required=False)

    class Meta:
        model = Petition
        read_only_fields = ["id", "break_dates", "entity_months"]
        fields = "__all__"


class BehaviorSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Behavior
        fields = "__all__"
