# -*- coding: utf-8 -*-
from rest_framework import serializers

from data_param.models import (
    DataGroup, Collection, FinalField, DataType, CleanFunction,
    ParameterGroup)


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

