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
    petition_id = serializers.IntegerField(
        source="data_file.petition_file_control.petition.id", read_only=True)
    file_control_id = serializers.IntegerField(
        source="data_file.petition_file_control.file_control.id", read_only=True)

    class Meta:
        model = AsyncTask
        # fields = "__all__"
        #exclude = ["result", "petition_id", "file_control_id"]
        exclude = ["result"]


class TaskFunctionSerializer(serializers.ModelSerializer):
    model_public_name = serializers.SerializerMethodField()

    def get_model_public_name(self, obj):
        return obj.get_model_name_display()

    class Meta:
        model = TaskFunction
        fields = "__all__"
