from rest_framework import serializers

from medicine.models import Component, Presentation, Container


class BasicComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = "__all__"


class BasicPresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = "__all__"


class BasicContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = "__all__"


class PresentationComponetSerializer(BasicPresentationSerializer):
    component = BasicComponentSerializer()


class PresentationContainersSerializer(BasicPresentationSerializer):
    containers = BasicContainerSerializer(many=True)


class FullComponentSerializer(serializers.ModelSerializer):
    presentations = PresentationContainersSerializer(many=True)

    class Meta:
        model = Component
        fields = "__all__"


class FullPresentationSerializer(
    PresentationContainersSerializer, PresentationComponetSerializer
):
    pass


class FullContainerSerializer(BasicContainerSerializer):
    presentation = PresentationComponetSerializer()
