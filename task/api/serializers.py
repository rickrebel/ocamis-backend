from rest_framework import serializers

from task.models import AsyncTask, CutOff, Step, ClickHistory, OfflineTask
from classify_task.models import StatusTask, TaskFunction, Stage
from datetime import timedelta


class StatusTaskSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = StatusTask
        fields = "__all__"


class AsyncTaskSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = AsyncTask
        exclude = ["result", "original_request"]


class AsyncTaskSerializer(serializers.ModelSerializer):
    # agency_id = serializers.IntegerField(source="data_file.petition_file_control.petition.agency.id")
    # prev_petition_id = serializers.IntegerField(
    #     source="data_file.petition_file_control.petition_id", read_only=True)
    petition_id = serializers.SerializerMethodField(read_only=True)
    file_control_id = serializers.IntegerField(
        source="data_file.petition_file_control.file_control_id", read_only=True)
    data_file_id = serializers.IntegerField(
        source="sheet_file.data_file_id", read_only=True)
    petition_file_control_id = serializers.IntegerField(
        source="data_file.petition_file_control_id", read_only=True)
    entity_month_id = serializers.IntegerField(
        source="entity_week.entity_month_id", read_only=True)
    entity_id = serializers.IntegerField(
        source="entity_month.entity_id", read_only=True)

    def get_petition_id(self, obj):
        if obj.data_file:
            return obj.data_file.petition_file_control.petition_id
        elif obj.reply_file:
            return obj.reply_file.petition_id
        elif obj.file_control:
            pfc = obj.file_control.petition_file_control.first()
            if pfc:
                return pfc.petition_id
        return None

    class Meta:
        model = AsyncTask
        # fields = "__all__"
        exclude = ["result", "original_request", "traceback"]


class AsyncTaskFullSerializer(AsyncTaskSerializer):
    # from inai.api.serializers import DataFileFullSerializer
    # data_file_full = DataFileFullSerializer(read_only=True, source="data_file")
    from inai.api.serializers import DataFileSerializer
    data_file_full = DataFileSerializer(read_only=True, source="data_file")
    file_control_full = serializers.SerializerMethodField(read_only=True)
    entity_month_full = serializers.SerializerMethodField(read_only=True)

    def get_file_control_full(self, obj):
        from data_param.api.serializers import FileControlSerializer
        if not obj.file_control and not obj.data_file:
            return None
        file_control = obj.file_control or obj.data_file.petition_file_control.file_control
        # print("file_control", file_control)
        # print("serializer: \n", FileControlSerializer(file_control).data)
        return FileControlSerializer(file_control).data

    def get_entity_month_full(self, obj):
        from inai.api.serializers import EntityMonthFullSerializer
        function = obj.task_function
        if function.is_from_aws:
            return None
        if not obj.entity_month or function.model_name != "entity_month":
            return None
        return EntityMonthFullSerializer(obj.entity_month).data


class TaskFunctionSerializer(serializers.ModelSerializer):
    model_public_name = serializers.SerializerMethodField()

    def get_model_public_name(self, obj):
        return obj.get_model_name_display()

    class Meta:
        model = TaskFunction
        fields = "__all__"


class StageSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stage
        fields = "__all__"


class StepSerializer(serializers.ModelSerializer):

    class Meta:
        model = Step
        fields = "__all__"
        ordering = ["-stage__order"]
        read_only_fields = ["cut_off", "stage"]


class CutOffSerializer(serializers.ModelSerializer):
    from inai.api.serializers import EntityMonthSimpleSerializer
    steps = StepSerializer(many=True, read_only=True)
    last_entity_month = EntityMonthSimpleSerializer(read_only=True)

    class Meta:
        model = CutOff
        fields = "__all__"


class OfflineTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfflineTask
        fields = "__all__"


mandatory_fields = [
    "real_start", "real_end", "date_start", "activity_type", "date_end"]


class ActivitySerializer(serializers.ModelSerializer):
    real_start = serializers.SerializerMethodField()
    real_end = serializers.SerializerMethodField()
    date_end = serializers.SerializerMethodField()
    activity_type = serializers.SerializerMethodField()
    reals = (5, 10)
    start_field = "date_start"

    # def get_start_field(self, obj):
    #     self.start_field = "date_start"

    # def get_start_field(self, obj):
    #     if hasattr(obj, "date_start"):
    #         return "date_start"
    #     return "date"

    def get_real_start(self, obj):
        start = getattr(obj, self.start_field)
        return start - timedelta(minutes=self.reals[0])

    def get_real_end(self, obj):
        end = self.get_date_end(obj)
        return end + timedelta(minutes=self.reals[1])

    def get_date_end(self, obj):
        end = None
        if hasattr(obj, "date_end"):
            end = getattr(obj, "date_end")
        if not end:
            end = getattr(obj, self.start_field)
            end += timedelta(seconds=5)
        return end


class AsyncTaskActivitySerializer(ActivitySerializer):
    model_name = serializers.CharField(source="task_function.model_name")
    start_field = "date_start"

    def get_activity_type(self, obj):
        return "task"

    class Meta:
        model = AsyncTask
        fields = mandatory_fields + ["model_name"]


class ClickHistoryActivitySerializer(ActivitySerializer):
    reals = (3, 8)
    date_start = serializers.DateTimeField(source="date", read_only=True)
    model = serializers.SerializerMethodField()
    start_field = "date"

    def get_model(self, obj):
        models = ["file_control", "entity_month", "petition"]
        for model in models:
            if getattr(obj, model, None) is not None:
                return model

    def get_activity_type(self, obj):
        return "click"

    class Meta:
        model = ClickHistory
        fields = mandatory_fields + ["model"]


class OfflineTaskActivitySerializer(ActivitySerializer):
    reals = (8, 12)
    start_field = "date_start"
    offline_type = serializers.CharField(source="activity_type")

    def get_activity_type(self, obj):
        return "offline"

    class Meta:
        model = OfflineTask
        fields = mandatory_fields + ["name", "offline_type"]
