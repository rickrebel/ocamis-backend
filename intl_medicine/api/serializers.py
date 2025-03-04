from rest_framework import serializers

from intl_medicine.models import Respondent, PrioritizedComponent, GroupAnswer

from medicine.api.serializers import GroupSerializer
from medicine.models import Component


class ResponsesSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        return value.group_id


class RespondentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respondent
        fields = "__all__"


class RespondentSerializer(serializers.ModelSerializer):
    responses = ResponsesSerializer(many=True, read_only=True)

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


class GroupAnswerReportSerializer(serializers.ModelSerializer):
    was_changed = serializers.SerializerMethodField()
    respondent = RespondentSimpleSerializer()

    def get_was_changed(self, obj):
        # return obj.prioritized.filter(was_changed=True).count()
        prioritizes = obj.prioritized.filter(was_changed=True)
        return PrioritizedComponentSerializer(prioritizes, many=True).data

    class Meta:
        model = GroupAnswer
        fields = "__all__"


class GroupAnswerSerializer(serializers.ModelSerializer):
    components = serializers.SerializerMethodField()
    group = GroupSerializer()
    base = serializers.SerializerMethodField()
    prioritized = serializers.SerializerMethodField()
    respondents = serializers.SerializerMethodField()
    # changes = serializers.SerializerMethodField()

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

        direct_components = Component.objects\
            .filter(prioritizedcomponent__group_answer__respondent__isnull=True,
                    prioritizedcomponent__group_answer__group=obj.group)\
            .exclude(id__in=all_components.keys())

        for component in direct_components:
            all_components.setdefault(
                component.id, {
                    "name": component.name,
                    "component": component.id,
                    "presentations": []
                })

        return list(all_components.values())

    def get_respondents(self, obj):
        request = self.context.get("request")
        user = request.user
        if user.is_staff:
            answer_groups = GroupAnswer.objects\
                .filter(group=obj.group, respondent__isnull=False,
                        time_spent__isnull=False)\
                .prefetch_related("respondent", "prioritized")\
                .order_by("-time_spent")

            return GroupAnswerReportSerializer(answer_groups, many=True).data
        else:
            return None

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
