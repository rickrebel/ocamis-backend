from rest_framework import serializers

from task.models import StatusTask, AsyncTask, TaskFunction


class StatusTaskSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = StatusTask
        fields = "__all__"


class AsyncTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = AsyncTask
        fields = "__all__"


class AsyncTaskSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = AsyncTask
        fields = "__all__"
        exclude = ()


class AsyncTaskFullSerializer(serializers.ModelSerializer):
    from inai.api.serializers import DataFileSerializer
    data_file_full = DataFileSerializer(read_only=True, source="data_file")
    # entity_id = serializers.IntegerField(source="data_file.petition_file_control.petition.entity.id")
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


class TaskFunctionSerializer(serializers.ModelSerializer):
    model_public_name = serializers.SerializerMethodField()

    def get_model_public_name(self, obj):
        return obj.get_model_name_display()

    class Meta:
        model = TaskFunction
        fields = "__all__"
