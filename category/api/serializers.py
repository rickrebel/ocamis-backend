# -*- coding: utf-8 -*-
from rest_framework import serializers

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason,
    DateBreak, InvalidReason, FileFormat)
from transparency.models import Anomaly, TransparencyIndex, TransparencyLevel


class FileTypeSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileType
        fields = "__all__"


class StatusControlSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = StatusControl
        fields = "__all__"


class ColumnTypeSimpleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ColumnType
        fields = [
            "id",
            "description",
            "col_type_functions",
            "name",
            "order",
            "public_name",
        ]


class NegativeReasonSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = NegativeReason
        fields = "__all__"


class InvalidReasonSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvalidReason
        fields = "__all__"


class DateBreakSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DateBreak
        fields = "__all__"


class AnomalySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Anomaly
        fields = "__all__"


class FileFormatSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileFormat
        fields = "__all__"


class TransparencyLevelSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TransparencyLevel
        fields = "__all__"


class TransparencyIndexSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TransparencyIndex
        fields = "__all__"


class TransparencyIndexSerializer(serializers.ModelSerializer):
    levels = TransparencyLevelSimpleSerializer(many=True)

    class Meta:
        model = TransparencyIndex
        fields = "__all__"
