# -*- coding: utf-8 -*-
from rest_framework import serializers

from medicine.models import (
    Component, Presentation, Container,
    Group, PresentationType
)


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = "__all__"


class GroupStoryBlokSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source="id")

    class Meta:
        model = Group
        fields = ["name", "value"]


class PresentationTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PresentationType
        fields = "__all__"


class ContainerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Container
        fields = "__all__"


class PresentationSimpleSerializer(serializers.ModelSerializer):
    presentation_type = PresentationTypeSerializer()

    class Meta:
        model = Presentation
        fields = "__all__"


class PresentationSerializer(PresentationSimpleSerializer):
    containers = ContainerSerializer(many=True)

    class Meta:
        model = Presentation
        fields = "__all__"


class PresentationVizSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True)

    class Meta:
        model = Presentation
        fields = "__all__"


class ComponentFullSerializer(serializers.ModelSerializer):
    presentations = PresentationSerializer(many=True)

    class Meta:
        model = Component
        fields = "__all__"


class ComponentVizSerializer(serializers.ModelSerializer):
    presentations = PresentationVizSerializer(many=True)

    class Meta:
        model = Component
        fields = "__all__"


class ComponentVizAllSerializer(serializers.ModelSerializer):

    class Meta:
        model = Component
        fields = "__all__"


class ComponentStoryBlokSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source="id")

    class Meta:
        model = Component
        fields = ["name", "value"]


class ComponentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Component
        fields = [
            "id",
            "name",
            "short_name",
            "alias",
            "is_vaccine",
            "is_relevant",
            "frequency",
        ]


class ComponentRetrieveSerializer(serializers.ModelSerializer):
    presentations = PresentationSerializer(many=True)

    class Meta:
        model = Component
        fields = [
            "id",
            "name",
            "short_name",
            "alias",
            "is_vaccine",
            "is_relevant",
            "frequency",
            "presentations",
        ]
