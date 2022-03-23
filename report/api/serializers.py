# -*- coding: utf-8 -*-
from rest_framework import serializers

from report.models import (
    Report, Supply, TestimonyMedia, Disease,
    CovidReport, DosisCovid, Persona, ComplementReport)
from medicine.api.serializers import (
    ComponentFullSerializer, PresentationSerializer)
from catalog.api.serializers import (
    InstitutionSerializer, CLUESSerializer, StateSerializer,
    CLUESFullSerializer)


class SupplyListSerializer(serializers.ModelSerializer):
    create = serializers.DateTimeField(
        format="%d/%m/%Y", read_only=True, source="report.created")
    state = serializers.ReadOnlyField(source="report.state.id")
    institution = serializers.ReadOnlyField(source="report.institution.id")
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Supply
        fields = "__all__"
        read_only_fields = ["report"]


class DosisCovidListSerializer(serializers.ModelSerializer):
    state = serializers.ReadOnlyField(source="covid_report.state.id")
    municipality = serializers.ReadOnlyField(
        source="covid_report.municipality.id")
    id = serializers.IntegerField(required=False)

    class Meta:
        model = DosisCovid
        fields = "__all__"
        read_only_fields = ["covid_report"]


class TestimonyMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestimonyMedia
        fields = "__all__"


class PersonaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Persona
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    supplies = SupplyListSerializer(many=True)

    def create(self, validated_data):
        supplies_items = validated_data.pop('supplies', [])
        report = Report.objects.create(**validated_data)
        for supply_item in supplies_items:
            supply = Supply()
            supply.report = report
            # el validador de datos convierte los ids en objetos, pero el
            # validador del serializador no los acepta, por lo que hay que
            # sacarlos antes del validador del serializador
            if "component" in supply_item:
                supply.component = supply_item.pop("component")
            if "presentation" in supply_item:
                supply.presentation = supply_item.pop("presentation")

            serializer = SupplyListSerializer(supply, data=supply_item)
            if serializer.is_valid():
                serializer.save()
            else:
                print(serializer.errors)

        report.send_responsable()
        return report

    def update(self, instance, validated_data):
        supplies_items = validated_data.pop('supplies', [])
        super(ReportSerializer, self).update(instance, validated_data)
        actual_id_supplies = []
        for supply_item in supplies_items:

            if "id" in supply_item:
                supply = Supply.objects.filter(
                    id=supply_item["id"], report=instance).first()
                if not supply:
                    continue
            else:
                supply = Supply()
                supply.report = instance

            if "component" in supply_item:
                supply.component = supply_item.pop("component")
            if "presentation" in supply_item:
                supply.presentation = supply_item.pop("presentation")
            if "disease" in supply_item:
                supply.disease = supply_item.pop("disease")

            serializer = SupplyListSerializer(supply, data=supply_item)
            if serializer.is_valid():
                supply = serializer.save()
                actual_id_supplies.append(supply.id)
            else:
                print(serializer.errors)

        Supply.objects.filter(report=instance)\
            .exclude(id__in=actual_id_supplies).delete()
        return instance

    class Meta:
        model = Report
        fields = [
            "id", "state", "institution", "is_other",
            "institution_raw", "hospital_name_raw", "clues", "has_corruption",
            "informer_type",
            "disease_raw", "created",
            "want_litigation", "supplies", "age"
        ]
        read_only_fields = [
            "created", "validated",  # "origin_app",
            "validator",
            "validated_date", "pending"]


class ComplementReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = ComplementReport
        fields = "__all__"
        read_only_fields = [
            "validated", "validator", "validated_date", "pending", "key"]


class ReportSerializer2(serializers.ModelSerializer):
    supplies = SupplyListSerializer(many=True)
    persona = PersonaSerializer()
    complement = ComplementReportSerializer()

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["created", "supplies"]


class ReportSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["created", "supplies"]


class CovidReportSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = CovidReport
        fields = "__all__"
        read_only_fields = ["created", "dosis"]


class CovidReportSerializer(serializers.ModelSerializer):
    dosis = DosisCovidListSerializer(many=True, read_only=True)
    persona = PersonaSerializer()
    complement = ComplementReportSerializer()

    class Meta:
        model = CovidReport
        fields = "__all__"
        read_only_fields = ["created", "dosis"]


class ReportUpdateSerializer(ReportSerializer):
    supplies = SupplyListSerializer(many=True)

    class Meta:
        model = Report
        fields = ReportSerializer.Meta.fields
        read_only_fields = [
            "id", "informer_type", "disease_raw", "created",
            "want_litigation"]


class CovidReportUpdateSerializer(ReportSerializer):
    supplies = SupplyListSerializer(many=True)

    class Meta:
        model = Report
        fields = ReportSerializer.Meta.fields
        """read_only_fields = [
            "id", "has_corruption", "narration", "informer_name", "email",
            "phone", "informer_type", "disease_raw", "created", "trimester",
            "origin_app", "testimony", "want_litigation", "validator",
            "validated_date", "public_testimony", "session_ga"]"""


class SupplyFullNextSerializer(serializers.ModelSerializer):
    component = ComponentFullSerializer()
    presentation = PresentationSerializer()

    class Meta:
        model = Supply
        fields = "__all__"


class ReportNextSerializer(serializers.ModelSerializer):
    testimonies_media = TestimonyMediaSerializer(many=True)
    supplies = SupplyFullNextSerializer(many=True)
    clues = CLUESFullSerializer()

    class Meta:
        model = Report
        fields = "__all__"


class ReportListSerializer(serializers.ModelSerializer):
    month = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_month(self, obj):
        return obj.created.month

    def get_count(self, obj):
        return 1

    class Meta:
        model = Report
        fields = ["state", "institution", "month", "count"]


class SupplyPublicSerializer(serializers.ModelSerializer):
    component = ComponentFullSerializer()
    presentation = PresentationSerializer()

    class Meta:
        model = Supply
        fields = ["id", "component", "presentation"]


class ReportPublicListSerializer(serializers.ModelSerializer):
    state = StateSerializer()
    institution = InstitutionSerializer()
    clues = CLUESSerializer()
    supplies = SupplyPublicSerializer(many=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "state",
            "institution",
            "hospital_name_raw",
            "clues",
            "informer_type",
            "created",
            "supplies",
        ]


class ReportPublicListSimpleSerializer(serializers.ModelSerializer):
    state = StateSerializer()
    institution = InstitutionSerializer()
    clues = CLUESSerializer()

    class Meta:
        model = Report
        fields = [
            "id",
            "state",
            "institution",
            "hospital_name_raw",
            "clues",
            "informer_type",
            "created",
        ]


class DiseaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Disease
        fields = "__all__"
