from rest_framework import serializers

from respond.models import ReplyFile, TableFile, LapSheet, SheetFile, CrossingSheet, DataFile, Behavior


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


class SheetFileSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = SheetFile
        # fields = "__all__"
        exclude = ["sample_data", "error_process", "warnings"]


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
    sample_data = serializers.SerializerMethodField(read_only=True)

    def get_sample_data(self, obj):
        from respond.views import SampleFile
        sample_file = SampleFile()
        return sample_file.get_sample(obj)

    class Meta:
        model = SheetFile
        fields = "__all__"


class SheetFileTableSerializer(SheetFileSerializer):

    class Meta:
        model = SheetFile
        exclude = ["sample_data", "error_process", "warnings"]


class SheetFileEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = SheetFile
        # fields = "__all__"
        exclude = ["sample_data", "error_process", "warnings"]
        read_only_fields = ["file", "sheet_name", "data_file"]


class CrossingSheetSimpleSerializer(serializers.ModelSerializer):
    # name = serializers.ReadOnlyField(source="file.name")

    class Meta:
        model = CrossingSheet
        fields = ["sheet_file_1", "sheet_file_2", "duplicates_count",
                  "shared_count", "month_record"]


class DataFileSimpleSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")

    class Meta:
        model = DataFile
        fields = ["id", "name", "url"]


class DataFileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    has_sample_data = serializers.SerializerMethodField(read_only=True)
    short_name = serializers.SerializerMethodField(read_only=True)
    real_name = serializers.SerializerMethodField(read_only=True)
    directory_short = serializers.SerializerMethodField(read_only=True)
    petition = serializers.IntegerField(
        source="petition_file_control.petition_id", read_only=True)

    def get_has_sample_data(self, obj):
        return bool(obj.sheet_files.exists())

    def get_real_name(self, obj):
        return obj.file.name.split("/")[-1]

    def get_short_name(self, obj):
        real_name = obj.file.name.split("/")[-1]
        return f"{real_name[:25]}...{real_name[-15:]}" \
            if len(real_name) > 42 else real_name

    def get_directory_short(self, obj):
        if not obj.directory:
            return None
        real_name = obj.directory
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


class DataFileTableSerializer(DataFileSimpleSerializer):
    has_sample_data = serializers.SerializerMethodField(read_only=True)
    short_name = serializers.SerializerMethodField(read_only=True)
    real_name = serializers.SerializerMethodField(read_only=True)
    directory_short = serializers.SerializerMethodField(read_only=True)
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

    def get_directory_short(self, obj):
        if not obj.directory:
            return None
        real_name = obj.directory
        return f"{real_name[:25]}...{real_name[-15:]}" \
            if len(real_name) > 42 else real_name

    class Meta:
        model = DataFile
        read_only_fields = ["has_sample_data"]
        exclude = ('sample_data', )


class SheetFileTable2Serializer(SheetFileSimpleSerializer):
    data_file = DataFileTableSerializer(read_only=True)


class LapSheetTableSerializer(serializers.ModelSerializer):
    table_files = TableFileSerializer(read_only=True, many=True)
    sheet_file = SheetFileTable2Serializer(read_only=True)

    class Meta:
        model = LapSheet
        fields = "__all__"


class SheetFileMonthSerializer(SheetFileSimpleSerializer):
    name = serializers.ReadOnlyField(source="file.name")
    url = serializers.ReadOnlyField(source="file.url")
    table_sums = serializers.SerializerMethodField(read_only=True)
    month_table_sums = serializers.SerializerMethodField(read_only=True)
    data_file = DataFileSerializer(read_only=True)
    file_control = serializers.IntegerField(
        source="data_file.petition_file_control.file_control_id")

    def get_table_sums(self, obj):
        from django.db.models import Sum, F
        sum_fields = [
            "rx_count", "duplicates_count", "shared_count",
            "self_repeated_count"]
        if obj.rx_count:
            final_sums = {field: getattr(obj, field) for field in sum_fields}
            return final_sums
        sum_fields += ["drugs_count"]
        query_sums = [Sum(field) for field in sum_fields]
        # query_annotations = {field: Sum(field) for field in sum_fields}
        last_lap = obj.laps.filter(lap=0).first()
        if last_lap:
            result_sums = last_lap.table_files.filter(
                collection__isnull=True).aggregate(*query_sums)
            result_with_init_names = {
                field: result_sums[f"{field}__sum"] for field in sum_fields}
            return result_with_init_names
        else:
            return {field: 0 for field in sum_fields}

    def get_month_table_sums(self, obj):
        from django.db.models import Sum, F
        month_record = self.context.get("month_record")
        sum_fields = [
            "rx_count", "duplicates_count", "shared_count", "drugs_count",
            "self_repeated_count"]
        query_sums = [Sum(field) for field in sum_fields]
        last_lap = obj.laps.filter(lap=0).first()
        if last_lap:
            result_sums = last_lap.table_files\
                .filter(collection__isnull=True,
                        week_record__month_record=month_record)\
                .aggregate(*query_sums)
            return {field: result_sums[f"{field}__sum"] for field in sum_fields}
        else:
            return {field: 0 for field in sum_fields}

    class Meta:
        model = SheetFile
        # fields = "__all__"
        exclude = ["sample_data", "error_process", "warnings"]


class BehaviorSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Behavior
        fields = "__all__"

