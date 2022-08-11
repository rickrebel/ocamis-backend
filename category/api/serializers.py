# -*- coding: utf-8 -*-
from rest_framework import serializers

from category.models import (
    FileType, StatusControl, ColumnType, NegativeReason, DateBreak, Anomaly)


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
        fields = "__all__"


class NegativeReasonSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = NegativeReason
        fields = "__all__"


class DateBreakSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DateBreak
        fields = "__all__"


class AnomalySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Anomaly
        fields = "__all__"

