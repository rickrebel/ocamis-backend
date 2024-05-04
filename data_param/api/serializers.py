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
    # clean_function = CleanFunctionSimpleSerializer()

    class Meta:
        model = Transformation
        fields = "__all__"


class NameColumnSerializer(serializers.ModelSerializer):
    # data_type = DataTypeSimpleSerializer()
    # column_type = ColumnTypeSimpleSerializer()
    # final_field = FinalFieldSimpleSerializer()
    transformations = TransformationSerializer(
        many=True, source="column_transformations")

    class Meta:
        model = NameColumn
        fields = "__all__"


class NameColumnHeadersSerializer(serializers.ModelSerializer):
    transformations = TransformationSerializer(
        many=True, source="column_transformations")
    parameter_group = serializers.IntegerField(
        source="final_field.parameter_group_id", read_only=True)
    provider = serializers.IntegerField(
        source="file_control.agency.provider_id", read_only=True)

    class Meta:
        model = NameColumn
        fields = ["column_type", "final_field", "data_type", "parameter_group",
                  "transformations", "std_name_in_data", "provider"]


class FileControlSimpleSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer(read_only=True)

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
    summary_status = serializers.SerializerMethodField(read_only=True)
    example_file_id = serializers.SerializerMethodField(read_only=True)

    def get_summary_status(self, obj):
        from respond.models import DataFile
        from django.db.models import Count, F
        files = DataFile.objects\
            .filter(petition_file_control__file_control=obj)\
            .values("status_id", "stage_id", "status__order", "stage__order")\
            .annotate(total=Count("id"))
        files = sorted(files, key=lambda x: (x["stage__order"], x["status__order"]))
        return list(files)

    def get_example_file_id(self, obj):
        from respond.models import SheetFile
        last_sheet_file = SheetFile.objects\
            .filter(data_file__petition_file_control__file_control=obj)\
            .order_by(
                "matched",
                "-data_file__stage__order",
                "-data_file__status__order",
            )\
            .first()
        # print("last_sheet_file", last_sheet_file)
        if last_sheet_file:
            return last_sheet_file.data_file_id
        return None


class FileControlSemiFullSerializer(FileControlSerializer):
    columns = NameColumnSerializer(many=True)
    real_columns = serializers.IntegerField(read_only=True)

    class Meta:
        model = FileControl
        fields = "__all__"
