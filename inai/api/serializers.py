from rest_framework import serializers

from data_param.api.serializers import FileControlSerializer, NameColumnSerializer
from inai.models import (
    Petition, PetitionFileControl, DataFile, MonthEntity, PetitionMonth,
    ProcessFile, PetitionBreak, PetitionNegativeReason)
from data_param.models import Transformation, NameColumn, FileControl

from category.api.serializers import (
    NegativeReasonSimpleSerializer)


class ProcessFileSerializer(serializers.ModelSerializer):
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


class TransformationEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transformation
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


def get_has_sample_data(obj):
    return bool(obj.sample_data)


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
    #child_files = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    has_sample_data = serializers.SerializerMethodField(read_only=True)
    short_name = serializers.SerializerMethodField(read_only=True)
    real_name = serializers.SerializerMethodField(read_only=True)
    petition = serializers.IntegerField(
        source="petition_file_control.petition_id", read_only=True)

    def get_has_sample_data(self, obj):
        return bool(obj.sample_data)

    def get_real_name(self, obj):
        return obj.file.name.split("/")[-1]

    def get_short_name(self, obj):
        real_name = obj.file.name.split("/")[-1]
        return f"{real_name[:25]}...{real_name[-15:]}" \
            if len(real_name) > 42 else real_name

    class Meta:
        model = DataFile
        #fields = "__all__"
        read_only_fields = ["has_sample_data"]
        exclude = ('sample_data', )


class DataFileEditSerializer(DataFileSerializer):

    class Meta:
        model = DataFile
        fields = "__all__"
        read_only_fields = ["petition_file_control", "file"]


class PetitionMonthSerializer(serializers.ModelSerializer):
    month_entity = MonthEntitySimpleSerializer(read_only=True)

    class Meta:
        model = PetitionMonth
        fields = "__all__"


"""class PetitionMiniSerializer(serializers.ModelSerializer):
    petition_months = PetitionMonthSerializer(many=True)
    #entity = serializers.SerializerMethodField(read_only=True)
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
        fields = "__all__" """


class PetitionFileControlCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        read_only_fields = ["data_files"]


class PetitionFileControlSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        #read_only_fields = ["file_control", "petition"]


class PetitionFileControlFullSerializer(PetitionFileControlSerializer):
    #file_control = FileControlSimpleSerializer()
    data_files = DataFileSerializer(many=True)

    class Meta:
        model = PetitionFileControl
        fields = "__all__"


class FileControlFullSerializer(FileControlSerializer):
    petition_file_control = PetitionFileControlFullSerializer(
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
    petition_months = PetitionMonthSerializer(many=True)
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
    process_files = ProcessFileSerializer(many=True)
    petition_file_controls = PetitionFileControlFullSerializer(
        many=True, source="file_controls")


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
