# -*- coding: utf-8 -*-
from rest_framework import serializers

from files_categories.models import (
    TypeFile, StatusControl, ColumnType, NegativeReason)


class TypeFileSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeFile
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

