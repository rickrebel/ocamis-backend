# -*- coding: utf-8 -*-
from rest_framework import serializers

from inai.models import (
    Petition, PetitionFileControl, PetitionMonth, MonthEntity)
from data_param.models import FileControl, NameColumn

from category.models import StatusControl, FileType
from category.api.serializers import (
    FileTypeSimpleSerializer, StatusControlSimpleSerializer)

from data_param.api.serializers import (
    DataGroupSimpleSerializer, FinalFieldVizSerializer)

from inai.api.serializers import (
    PetitionMonthSerializer, PetitionNegativeReasonSimpleSerializer)


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


class NameColumnViz3Serializer(serializers.ModelSerializer):
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
            (value.final_field.collection.model_name, value.final_field.name))


class AnomaliesVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        #return (value.name)
        return (value.id)


class EntityCLUESVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        #return (value.name)
        return value.petition.entity.clues_id


class EntityViz2Serializer(serializers.RelatedField):
    def to_representation(self, value):
        #return (value.name)
        return value.petition.entity_id


class FileControlViz2Serializer(serializers.ModelSerializer):
    #data_group = DataGroupSimpleSerializer(read_only=True)
    columns = NameColumnVizSerializer(many=True, read_only=True,)
    anomalies = AnomaliesVizSerializer(many=True, read_only=True)
    petition_file_control = EntityCLUESVizSerializer(many=True, read_only=True)
    entities = EntityViz2Serializer(
        many=True, read_only=True, source="petition_file_control")
    #format_file = serializers.ReadOnlyField(source="file_format_id")

    class Meta:
        model = FileControl
        fields = [
            "id",
            "format_file",
            "file_format",
            "anomalies",
            "name",
            #"data_group",
            "columns",
            "petition_file_control",
            "entities"
        ]


class PetitionFileControlVizSerializer(serializers.ModelSerializer):
    data_group = DataGroupSimpleSerializer(
        read_only=True, source="file_control.data_group")
    columns = NameColumnVizSerializer(
        many=True, read_only=True, source="file_control.columns")
    anomalies = AnomaliesVizSerializer(
        many=True, read_only=True, source="file_control.anomalies")
    format_file = serializers.ReadOnlyField(source="file_control.file_format_id")
    #id = serializers.ReadOnlyField(source="file_control_id")

    class Meta:
        model = FileControl
        fields = [
            #"id"
            "format_file",
            "anomalies",
            "data_group",
            "columns",
        ]


class PetitionFilesControlViz3Serializer(serializers.RelatedField):
    def to_representation(self, value):
        return (value.file_control_id)


class StatusDataVizSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return (value.name)


"""
    class Meta:
        model = PetitionFileControl
        fields = "__all__"
        read_only_fields = ["file_control"]
"""


class PetitionVizSerializer(serializers.ModelSerializer):
    #file_controls = PetitionFileControlVizSerializer(many=True)
    file_controls = PetitionFilesControlViz3Serializer(many=True, read_only=True)
    #status_data = serializers.CharField(source="name", read_only=True)
    status_data = StatusDataVizSerializer(read_only=True)
    status_petition = StatusDataVizSerializer(read_only=True)
    #status_petition = StatusControlSimpleSerializer()
    #invalid_reason = InvalidReasonSimpleSerializer()
    negative_reasons = PetitionNegativeReasonSimpleSerializer(many=True)
    #petition_months = PetitionMonthSerializer(many=True)
    months = PetitionMonthVizSerializer(
        many=True, read_only=True, source="petition_months")

    class Meta:
        model = Petition
        fields = [
            "id",
            "entity",
            "folio_petition",
            "file_controls",
            "status_data",
            "status_petition",
            "send_petition",
            "months",
            "negative_reasons",
            "invalid_reason",
            #"months",
        ]
