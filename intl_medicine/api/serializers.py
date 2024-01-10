from rest_framework import serializers

from intl_medicine.models import Respondent, PrioritizedComponent, GroupAnswer

from medicine.api.serializers import GroupSerializer
from medicine.models import Group


class ResponsesSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        return value.group_id


class RespondentSerializer(serializers.ModelSerializer):
    responses = ResponsesSerializer(
        source="presentations", many=True, read_only=True)

    class Meta:
        model = Respondent
        fields = "__all__"
        read_only_fields = ('token', 'presentations')


class PrioritizedComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrioritizedComponent
        fields = "__all__"


class GroupAnswerSimpleSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = GroupAnswer
        fields = "__all__"


class GroupAnswerSerializer(serializers.ModelSerializer):
    components = serializers.SerializerMethodField()
    group = GroupSerializer()
    base = serializers.SerializerMethodField()
    prioritized = serializers.SerializerMethodField()

    def get_components(self, obj):
        presentations = obj.group.presentations.all()\
            .prefetch_related("component", "presentation_type") \
            .order_by("component__name")
        all_components = {}
        for presentation in presentations:
            comp_id = presentation.component_id
            all_components.setdefault(
                comp_id, {
                    "name": presentation.component.name,
                    "component": comp_id,
                    "presentations": []
                })
            current_presentation = {
                "presentation_id": presentation.id,
                "presentation_type": presentation.presentation_type.name,
                "description": presentation.description,
                "component_id": comp_id,
                "sub_group": presentation.group_id
            }
            all_components[comp_id]["presentations"].append(
                current_presentation)

        return list(all_components.values())

    def get_base(self, obj):
        prior_group_answer = GroupAnswer.objects.filter(
            group=obj.group, respondent__isnull=True).first()
        priors = prior_group_answer.prioritized.all()
        return PrioritizedComponentSerializer(priors, many=True).data

    def get_prioritized(self, obj):
        priors = obj.prioritized.all()
        return PrioritizedComponentSerializer(priors, many=True).data

    class Meta:
        model = GroupAnswer
        fields = "__all__"
