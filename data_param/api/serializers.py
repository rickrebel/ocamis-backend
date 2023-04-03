# -*- coding: utf-8 -*-
from rest_framework import serializers

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction,
    ParameterGroup, Transformation, NameColumn, FileControl)


class CollectionSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Collection
        fields = "__all__"


class FinalFieldSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinalField
        fields = "__all__"


class FinalFieldVizSerializer(serializers.ModelSerializer):
    collection = CollectionSimpleSerializer()

    class Meta:
        model = FinalField
        fields = "__all__"


class DataGroupSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataGroup
        fields = "__all__"


class DataGroupFullSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataGroup
        fields = "__all__"



class DataTypeSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataType
        fields = "__all__"


class CleanFunctionSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = CleanFunction
        fields = "__all__"


class ParameterGroupSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParameterGroup
        fields = "__all__"


class TransformationSerializer(serializers.ModelSerializer):
    #clean_function = CleanFunctionSimpleSerializer()

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


class FileControlSimpleSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer(read_only=True)
    #file_type = FileTypeSimpleSerializer(read_only=True)
    #status_register = StatusControlSimpleSerializer(read_only=True)

    class Meta:
        model = FileControl
        fields = "__all__"


class FileControlSerializer(FileControlSimpleSerializer):
    # from category.models import FileType
    from data_param.models import DataGroup
    name = serializers.CharField(required=False)
    transformations = TransformationSerializer(
        many=True, source="file_transformations", read_only=True)
    data_group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="data_group",
        queryset=DataGroup.objects.all(), required=False)
    # file_type_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="file_type",
    #     queryset=FileType.objects.all())
    # status_register_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True, source="status_register",
    #     queryset=StatusControl.objects.all())
    summary_status = serializers.SerializerMethodField(read_only=True)
    failed_files = serializers.SerializerMethodField(read_only=True)

    def get_summary_status(self, obj):
        from inai.models import DataFile
        from django.db.models import Count, F
        files = DataFile.objects\
            .filter(petition_file_control__file_control=obj)\
            .values("status_id", "stage_id")\
            .annotate(total=Count("id"))
        return list(files)

    def get_failed_files(self, obj):
        from inai.models import DataFile
        from django.db.models import Count, F
        files = DataFile.objects\
            .filter(petition_file_control__file_control=obj)\
            .values("status_process_id")\
            .annotate(total=Count("id"))
        return list(files)


class FileControlSemiFullSerializer(FileControlSerializer):
    columns = NameColumnSerializer(many=True)

    class Meta:
        model = FileControl
        fields = "__all__"
