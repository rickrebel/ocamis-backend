# -*- coding: utf-8 -*-
from rest_framework import serializers

from report.models import (
    Report, Supply, Responsable, TestimonyMedia, Disease)
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


class TestimonyMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestimonyMedia
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
            "id", "state", "disease_raw", "institution", "is_other",
            "institution_raw", "hospital_name_raw", "clues", "has_corruption",
            "narration", "informer_name", "email", "phone", "informer_type",
            "disease_raw", "created", "trimester", "validated", "origin_app",
            "testimony", "want_litigation", "validator", "validated_date",
            "pending", "public_testimony", "supplies", "session_ga", "age"
        ]
        read_only_fields = [
            "created", "validated",  # "origin_app",
            "validator",
            "validated_date", "pending"]


class ReportUpdateSerializer(ReportSerializer):
    supplies = SupplyListSerializer(many=True)

    class Meta:
        model = Report
        fields = ReportSerializer.Meta.fields
        read_only_fields = [
            "id", "has_corruption", "narration", "informer_name", "email",
            "phone", "informer_type", "disease_raw", "created", "trimester",
            "origin_app", "testimony", "want_litigation", "validator",
            "validated_date", "public_testimony", "session_ga"]


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
