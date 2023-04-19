from rest_framework import serializers

from task.models import AsyncTask
from classify_task.models import StatusTask, TaskFunction, Stage


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
        source="data_file.origin_file_id", read_only=True)
    petition_file_control_id = serializers.IntegerField(
        source="data_file.petition_file_control_id", read_only=True)

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
        exclude = ["result", "original_request"]


class AsyncTaskFullSerializer(AsyncTaskSerializer):
    # from inai.api.serializers import DataFileFullSerializer
    # data_file_full = DataFileFullSerializer(read_only=True, source="data_file")
    from inai.api.serializers import DataFileSerializer
    data_file_full = DataFileSerializer(read_only=True, source="data_file")
    file_control_full = serializers.SerializerMethodField(read_only=True)

    def get_file_control_full(self, obj):
        from data_param.api.serializers import FileControlSerializer
        if not obj.file_control and not obj.data_file:
            return None
        file_control = obj.file_control or obj.data_file.petition_file_control.file_control
        # print("file_control", file_control)
        # print("serializer: \n", FileControlSerializer(file_control).data)
        return FileControlSerializer(file_control).data


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
