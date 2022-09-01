# -*- coding: utf-8 -*-
from rest_framework import serializers

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason,
    DateBreak, Anomaly, InvalidReason)


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

