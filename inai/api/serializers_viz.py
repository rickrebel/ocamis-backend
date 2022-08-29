# -*- coding: utf-8 -*-
from rest_framework import serializers

from inai.models import (
    FileControl, Petition, PetitionFileControl, PetitionMonth, NameColumn,
    MonthEntity)

from category.models import StatusControl, FileType
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer)

from data_param.api.serializers import (
    DataGroupSimpleSerializer, FinalFieldVizSerializer)

from inai.api.serializers import PetitionMonthSerializer


class PetitionMonthVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return value.month_entity.year_month


class MonthEntityVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return value.year_month


class NameColumnViz2Serializer(serializers.ModelSerializer):
    final_field = FinalFieldVizSerializer()

    class Meta:
        model = NameColumn
        fields = "__all__"


class NameColumnVi3zSerializer(serializers.ModelSerializer):
    #final_field = FinalFieldVizSerializer()
    final_field = serializers.CharField(
        source="final_field__name", read_only=True)
    collection = serializers.ReadOnlyField(
        source="final_field__collection__model_name")

    class Meta:
        model = NameColumn
        fields = ["final_field", "collection"]


class NameColumnVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return ((None, None) if not value.final_field else
            (value.final_field.name, value.final_field.collection.model_name))


class AnomaliesVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return (value.name)


class PetitionFileControlVizSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer(
        read_only=True, source="file_control.data_group")
    columns = NameColumnVizSerializer(
        many=True, read_only=True, source="file_control.columns")
    anomalies = AnomaliesVizSerializer(
        many=True, read_only=True, source="file_control.anomalies")
    format_file = serializers.ReadOnlyField(source="file_control.format_file")

    class Meta:
        model = FileControl
        fields = [
            "format_file",
            "anomalies",
            "data_group",
            "columns",
        ]


    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        read_only_fields = ["file_control"]


class PetitionVizSerializer(serializers.ModelSerializer):
    file_controls = PetitionFileControlVizSerializer(many=True)
    status_data = StatusControlSimpleSerializer()
    status_petition = StatusControlSimpleSerializer()
    #petition_months = PetitionMonthSerializer(many=True)
    months = PetitionMonthVizSerializer(
        many=True, read_only=True, source="petition_months")

    class Meta:
        model = Petition
        fields = [
            "id",
            "folio_petition",
            "file_controls",
            "status_data",
            "status_petition",
            "months",
            #"months",
        ]
