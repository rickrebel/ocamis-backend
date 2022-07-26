# -*- coding: utf-8 -*-
from rest_framework import serializers

from parameter.models import (
    GroupData, Collection, FinalField, TypeData, CleanFunction)


class GroupDataSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupData
        fields = "__all__"


class CollectionSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Collection
        fields = "__all__"


class FinalFieldSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinalField
        fields = "__all__"


class TypeDataSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeData
        fields = "__all__"


class CleanFunctionSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = CleanFunction
        fields = "__all__"
