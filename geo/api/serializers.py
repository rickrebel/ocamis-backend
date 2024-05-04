from rest_framework import serializers

from geo.models import (
    State, Institution, CLUES, Municipality, Agency,
    Provider, Delegation)
from task.api.serializers import CutOffSerializer
# from report.api.serializers import ResponsableListSerializer
# from inai.models import MonthRecord


class MunicipalityListSerializers(serializers.ModelSerializer):

    class Meta:
        model = Municipality
        fields = "__all__"


class StateSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = "__all__"


class StateSerializer(serializers.ModelSerializer):
    municipalities = MunicipalityListSerializers(many=True)

    class Meta:
        model = State
        fields = "__all__"


class StateListSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = "__all__"


class InstitutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Institution
        fields = "__all__"


class InstitutionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Institution
        fields = "__all__"


class CLUESSerializer(serializers.ModelSerializer):

    class Meta:
        model = CLUES
        fields = ['id', 'name', 'real_name', 'alter_clasifs',
                  'prev_clasif_name', 'clasif_name', 'number_unity',
                  'total_unities', 'municipality']


class ProviderCatSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    state = StateSimpleSerializer(read_only=True)
    clues = CLUESSerializer(read_only=True, source="ent_clues", many=True)
    cut_offs = CutOffSerializer(many=True)

    class Meta:
        model = Provider
        fields = [
            "id", "institution", "state", "clues", "name", "provider_type",
            "acronym", "notes", "assigned_to", "status_operative",
            "cut_offs", "is_indirect", "has_indirect"]


class ProviderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Provider
        fields = "__all__"
        read_only_fields = ["name", "acronym"]


class CLUESListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CLUES
        fields = ['id', 'name', 'real_name', 'alter_clasifs',
                  'prev_clasif_name', 'clasif_name', 'number_unity',
                  'total_unities', 'municipality', "responsables"]


class CLUESFullSerializer(serializers.ModelSerializer):

    class Meta:
        model = CLUES
        fields = "__all__"
        depth = 1


class AgencySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    state = StateSimpleSerializer(read_only=True)
    clues = CLUESSerializer(read_only=True)

    class Meta:
        model = Agency
        fields = [
            "id",
            "institution",
            "state",
            "provider",
            "clues",
            "name",
            "addl_params",
            "vigencia",
            "agency_type",
            "acronym",
            "notes",
            "is_pilot",
        ]


class AgencyFileControlsSerializer(serializers.ModelSerializer):
    file_controls = serializers.SerializerMethodField(read_only=True)
    
    def get_file_controls(self, obj):
        from data_param.models import FileControl
        from data_param.api.serializers import FileControlSemiFullSerializer
        queryset = FileControl.objects\
            .filter(agency=obj)\
            .distinct()\
            .order_by("data_group", "id")\
            .prefetch_related(
                "data_group",
                "columns",
                "columns__column_transformations",
            )
        return FileControlSemiFullSerializer(queryset, many=True).data

    class Meta:
        model = Agency
        fields = ["file_controls"]


class ProviderFileControlsSerializer(serializers.ModelSerializer):
    file_controls = serializers.SerializerMethodField(read_only=True)

    def get_file_controls(self, obj):
        from data_param.models import FileControl
        from data_param.api.serializers import FileControlSemiFullSerializer
        prefetch_related = [
            "data_group", "columns", "columns__column_transformations"]
        if obj.is_indirect:
            queryset = FileControl.objects\
                .filter(real_provider=obj)\
                .distinct()\
                .order_by("data_group", "id")\
                .prefetch_related(*prefetch_related)
        else:
            queryset = FileControl.objects\
                .filter(agency__provider=obj)\
                .distinct()\
                .order_by("data_group", "id")\
                .prefetch_related(*prefetch_related)
        return FileControlSemiFullSerializer(queryset, many=True).data

    class Meta:
        model = Provider
        fields = ["file_controls"]


def calc_drugs_summarize(obj, table_files=None):
    from django.db.models import Sum, F
    drugs_counts_by_week = obj.weeks \
        .values("month_record") \
        .annotate(drugs_count=Sum(F("drugs_count"))) \
        .values("month_record", "drugs_count")
    if not table_files:
        table_files = obj.table_files \
            .filter(week_record__isnull=False)
    drugs_count_by_drug = table_files \
        .exclude(collection__model_name="Rx") \
        .prefetch_related("collection", "lap_sheet__sheet_file__behavior") \
        .values(
            "week_record__month_record",
            "collection__model_name",
            "lap_sheet__sheet_file__behavior__is_discarded"
        ) \
        .annotate(
            drugs_count=Sum(F("drugs_count")),
            month_record=F("week_record__month_record"),
            collection=F("collection__model_name"),
            discarded=F("lap_sheet__sheet_file__behavior__is_discarded")) \
        .values("month_record", "drugs_count", "collection", "discarded")
    final_result = {}
    for drugs_count_by_week in drugs_counts_by_week:
        month_record = str(drugs_count_by_week["month_record"])
        final_result[month_record] = {
            "by_week": drugs_count_by_week["drugs_count"],
            "Drug": 0,
            "by_tables_included": 0,
            "by_tables_discarded": 0,
            "in_month": getattr(obj, "drugs_count", 0)
        }
    for drugs_count_by_drug in drugs_count_by_drug:
        month_record = drugs_count_by_drug["month_record"]
        collection = drugs_count_by_drug["collection"]
        if collection == "Drug":
            field = "Drug"
        else:
            field = "by_tables_included"
            if drugs_count_by_drug["discarded"]:
                field = "by_tables_discarded"
        month_record = str(month_record)
        if not final_result.get(month_record):
            final_result[month_record] = {}
        # print("final_result\n", final_result, "\n")
        # print("month_record", month_record)
        # print("type of month_record", type(month_record))
        # print("final_result[month_record]", final_result[month_record])
        # print("field", field)
        # print("drugs_count_by_drug[drugs_count]", drugs_count_by_drug["drugs_count"])
        final_result[month_record][field] = drugs_count_by_drug["drugs_count"]
    return final_result


def calc_sheet_files_summarize(provider, month_record=None):
    from django.db.models import Count
    from inai.models import MonthRecord
    count_by_year_month_and_behavior = []
    if month_record:
        all_month_records = [month_record]
    else:
        all_month_records = MonthRecord.objects\
            .filter(provider=provider)\
            .order_by("year_month")
    for month_record in all_month_records:
        behavior_counts = month_record.sheet_files\
            .filter(behavior__isnull=False)\
            .values("behavior")\
            .annotate(count=Count("behavior"))
        for behavior_count in behavior_counts:
            count_by_year_month_and_behavior.append({
                "year_month": month_record.year_month,
                "behavior": behavior_count["behavior"],
                "count": behavior_count["count"]
            })
    return count_by_year_month_and_behavior


class ProviderFullSerializer(ProviderCatSerializer, ProviderFileControlsSerializer):
    from inai.api.serializers import (
        MonthRecordSerializer, RequestTemplateSerializer)

    # petitions = PetitionSemiFullSerializer(many=True)
    petitions = serializers.SerializerMethodField(read_only=True)
    month_records = MonthRecordSerializer(many=True)
    sheet_files_summarize = serializers.SerializerMethodField(read_only=True)
    drugs_summarize = serializers.SerializerMethodField(read_only=True)
    last_request_template = serializers.SerializerMethodField(read_only=True)
    provider_templates = RequestTemplateSerializer(
        many=True, source="request_templates")

    def get_petitions(self, obj):
        from inai.api.serializers import PetitionSemiFullSerializer
        from inai.models import Petition
        prefetch_related = [
            "file_controls", "agency", "break_dates",
            "negative_reasons", "negative_reasons__negative_reason",
            "reply_files"]
        if obj.is_indirect:
            petitions = Petition.objects\
                .filter(real_provider=obj)\
                .prefetch_related(*prefetch_related)
        else:
            petitions = Petition.objects\
                .filter(agency__provider=obj)\
                .prefetch_related(*prefetch_related)
        serializer = PetitionSemiFullSerializer(petitions, many=True)
        return serializer.data

    def get_sheet_files_summarize(self, obj):
        return calc_sheet_files_summarize(obj)

    def get_drugs_summarize(self, obj):
        return calc_drugs_summarize(obj)

    def get_last_request_template(self, obj):
        from inai.models import RequestTemplate
        from inai.api.serializers import RequestTemplateSerializer
        last_request_template = RequestTemplate.objects\
            .filter(provider=obj)\
            .order_by("-id")\
            .first()
        if last_request_template:
            return RequestTemplateSerializer(last_request_template).data
        return None

    class Meta:
        model = Provider
        fields = "__all__"


class AgencyVizSerializer(AgencySerializer):
    # from inai.api.serializers import MonthRecordSimpleSerializer
    from inai.api.serializers_viz import (
        PetitionVizSerializer, MonthRecordVizSerializer)

    agency_type = serializers.ReadOnlyField()
    petitions = PetitionVizSerializer(many=True)
    months = MonthRecordVizSerializer(
        many=True, read_only=True, source="provider.month_records")
    # months = serializers.SerializerMethodField(read_only=True)

    # def get_months(self, obj):
    #    return MonthRecord.objects.filter(agency=obj)\
    #        .values_list("year_month", flat=True).distinct()

    class Meta:
        model = Agency
        fields = [
            "id",
            "name",
            "acronym",
            "is_pilot",
            "institution",
            "state",
            "clues",
            "provider",
            "agency_type",
            "petitions",
            "months",
            "population",
        ]


class DelegationVizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Delegation
        fields = "__all__"
