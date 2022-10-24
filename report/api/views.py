# -*- coding: utf-8 -*-
from xlsx_export.generic import GenericModelExport
from . import serializers
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
from rest_framework.exceptions import (
    PermissionDenied, ValidationError)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from report.models import (
    Report, Supply, CovidReport, DosisCovid, Persona,
    ComplementReport)

from api.mixins import (MultiSerializerListCreateRetrieveUpdateMix as
                        ListCreateRetrieveUpdateMix, ListMix)

from catalog.models import State, Institution, Alliances, Disease
from catalog.api.serializers import (
    StateListSerializer, InstitutionSerializer, AlliancesSerializer,
    DiseaseSerializer)
# --------Paginacion-----------------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 1000
# -----------------------------------------------------------------------------


class HeavyResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
# -----------------------------------------------------------------------------


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        data = {
            "states": StateListSerializer(
                State.objects.all(), many=True).data,
            "institutions": InstitutionSerializer(
                Institution.objects.all().order_by("relevance"),
                many=True).data,
            "alliances": AlliancesSerializer(
                Alliances.objects.all().order_by("name"),
                many=True, context={"request": request}).data,
            "diseases": DiseaseSerializer(
                Disease.objects.all().order_by("name"),
                many=True, context={"request": request}).data
        }
        return Response(data)


class SupplyList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.SupplyListSerializer
    queryset = Supply.objects.all()
    pagination_class = StandardResultsSetPagination


class IsAdminOrCreateOnly(BasePermission):

    def has_permission(self, request, view):
        print(view.action)
        if view.action == 'create':
            return True
        else:
            return request.user.is_staff


class ComplementPermission(BasePermission):

    def has_permission(self, request, view):
        print("request", request)
        print("view", view)
        print("view.action", view.action)
        key = request.query_params.get("key", None)
        compl_id = view.kwargs.get("pk", None)

        if view.action == 'update' and key:
            try:
                complement = ComplementReport.objects.get(
                    key=key, id=compl_id)
            except Exception as e:
                print(e)
                return False
            view.complement = complement
            return True
        else:
            return request.user.is_staff


class ReportView(ListCreateRetrieveUpdateMix):
    #permission_classes = (IsAdminOrCreateOnly,)
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.ReportSerializer
    queryset = Report.objects.all()
    pagination_class = HeavyResultsSetPagination
    action_serializers = {
        "update": serializers.ReportUpdateSerializer
    }

    def update(self, request, **kwargs):
        from django.utils import timezone
        self.check_permissions(request)
        report = self.get_object()
        report.validator = request.user.id
        report.validated_date = timezone.now()
        serializer = self.get_serializer_class()(report, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False, url_path='next')
    def next(self, request, **kwargs):
        from datetime import timedelta
        if not request.user.is_staff:
            raise PermissionDenied()
        query_kwargs = {"validated__isnull": True}
        pending = request.query_params.get("pending")
        if pending:
            if pending.lower() in ["si", "yes", "true"]:
                query_kwargs["pending"] = True
            elif pending.lower() in ["no", "false"]:
                query_kwargs["pending"] = False
        else:
            query_kwargs["pending"] = False
        report = Report.objects.filter(**query_kwargs)\
            .order_by("created").first()

        if not report:
            return Response(status=status.HTTP_204_NO_CONTENT)
        many_reports_1 = Report.objects.filter(**query_kwargs)\
            .filter(
                created__lte=(
                    report.created + timedelta(seconds=30 * 60)),
                email=report.email,
                clues=report.clues)\
            .order_by("created").distinct()
        many_reports_2 = Report.objects.filter(**query_kwargs)\
            .filter(
                created__lte=(
                    report.created + timedelta(seconds=8 * 60)),
                state=report.state,
                institution=report.institution,
                institution_raw=report.institution_raw)\
            .order_by("created").distinct()

        if many_reports_1.count() > 1:
            final_query = many_reports_1
        else:
            final_query = many_reports_2

        return Response(
            serializers.ReportNextSerializer(final_query, many=True).data)


class ReportView2(ListCreateRetrieveUpdateMix):
    permission_classes = (IsAdminOrCreateOnly,)
    #permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.ReportSerializer2
    queryset = Report.objects.all()
    pagination_class = HeavyResultsSetPagination
    action_serializers = {
        "update": serializers.ReportUpdateSerializer2,
        "create": serializers.ReportSimpleSerializer
    }

    def create(self, request, **kwargs):
        self.check_permissions(request)
        data_rep = request.data
        if data_rep.get('persona', False):
            persona_data = data_rep.pop('persona')
            pers = Persona()
            serializer_persona = serializers.PersonaSerializer(
                pers, data=persona_data)
            if serializer_persona.is_valid():
                persona = serializer_persona.save()
                data_rep["persona"] = persona.id
            else:
                return Response({"errors": serializer_persona.errors},
                                status=status.HTTP_400_BAD_REQUEST)

        new_report = Report()
        report = None
        supplies_items = data_rep.pop('supplies', [])
        serializer_rep = self.get_serializer_class()(
            new_report, data=data_rep)
        if serializer_rep.is_valid():
            report = serializer_rep.save()
        else:
            return Response({"errors": serializer_rep.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        data_rep["report"] = report.id
        complement_rep = ComplementReport()
        serializer_comp = serializers.ComplementReportSerializer(
            complement_rep, data=data_rep)
        if serializer_comp.is_valid():
            serializer_comp.save()
        else:
            return Response({"errors": serializer_comp.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        for supply_item in supplies_items:
            supply = Supply()
            supply.report = report

            serializer_supp = serializers.SupplyListSerializer(
                supply, data=supply_item)
            if serializer_supp.is_valid():
                serializer_supp.save()
            else:
                print(serializer_supp.errors)

        new_serializer = serializers.ReportSerializer2(
            report, context={'request': request})
        report.send_informer()
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, **kwargs):
        from django.utils import timezone
        self.check_permissions(request)
        print("ESTOY EN update")
        report = self.get_object()
        data_rep = request.data
        if data_rep.get('persona', False):
            persona_data = data_rep.pop('persona')
            pers = Persona.objects.get(id=report.persona.id)
            serializer_persona = serializers.PersonaSerializer(
                pers, data=persona_data)
            if serializer_persona.is_valid():
                serializer_persona.save()
            else:
                return Response({"errors": serializer_persona.errors},
                                status=status.HTTP_400_BAD_REQUEST)

        supplies_items = data_rep.pop('supplies', [])
        serializer = self.get_serializer_class()(report, data=data_rep)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response({"errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        complement_rep = ComplementReport.objects.get(report=report.id)
        complement_rep.validator = request.user.id
        complement_rep.validated_date = timezone.now()
        serializer_comp = serializers.ComplementReportUpdateSerializer(
            complement_rep, data=data_rep)
        if serializer_comp.is_valid():
            serializer_comp.save()
        else:
            print("Error en complement")
            return Response({"errors": serializer_comp.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        actual_id_supplies = []
        for supply_item in supplies_items:
            if "id" in supply_item:
                supply = Supply.objects.filter(
                    id=supply_item["id"], report=report).first()
                if not supply:
                    continue
            else:
                supply = Supply()
                supply.report = report

            """if "component" in supply_item:
                supply.component = supply_item.pop("component")
            if "presentation" in supply_item:
                supply.presentation = supply_item.pop("presentation")
            if "disease" in supply_item:
                supply.disease = supply_item.pop("disease")"""

            serializer_supp = serializers.SupplyListSerializer(
                supply, data=supply_item)
            if serializer_supp.is_valid():
                supply = serializer_supp.save()
                actual_id_supplies.append(supply.id)
            else:
                print(serializer_supp.errors)
        Supply.objects.filter(report=report)\
            .exclude(id__in=actual_id_supplies).delete()

        new_serializer = serializers.ReportSerializer2(
            report, context={'request': request})
        if data_rep["validated"] is True:
            report.send_responsable()
        return Response(
            new_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['get'], detail=False, url_path='next')
    def next(self, request, **kwargs):
        from datetime import timedelta
        if not request.user.is_staff:
            raise PermissionDenied()
        query_kwargs = {"complement__validated__isnull": True}
        pending = request.query_params.get("pending")
        if pending:
            if pending.lower() in ["si", "yes", "true"]:
                query_kwargs["complement__pending"] = True
            elif pending.lower() in ["no", "false"]:
                query_kwargs["complement__pending"] = False
        else:
            query_kwargs["complement__pending"] = False
        report = Report.objects.filter(**query_kwargs)\
            .order_by("created").first()

        if not report:
            return Response(status=status.HTTP_204_NO_CONTENT)
        many_reports_1 = Report.objects.filter(**query_kwargs)\
            .filter(
                created__lte=(
                    report.created + timedelta(seconds=30 * 60)),
                email=report.email,
                clues=report.clues)\
            .order_by("created").distinct()
        many_reports_2 = Report.objects.filter(**query_kwargs)\
            .filter(
                created__lte=(
                    report.created + timedelta(seconds=8 * 60)),
                state=report.state,
                institution=report.institution,
                institution_raw=report.institution_raw)\
            .order_by("created").distinct()

        if many_reports_1.count() > 1:
            final_query = many_reports_1
        else:
            final_query = many_reports_2

        return Response(
            serializers.ReportNextSerializer(final_query, many=True).data)

    @action(methods=["post"], detail=True, url_path='pending')
    def pending(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        pending = request.data.get("pending")
        validated = request.data.get("validated")
        report = self.get_object()
        complement = ComplementReport.objects.get(report=report)
        #print(report)
        errors = []

        if pending in [True, "true"]:
            complement.pending = True
        elif pending in [False, "false"]:
            complement.pending = False
        elif pending:
            errors.append("pending invalido")

        if validated in [True, "true"]:
            complement.validated = True
        elif validated in [False, "false"]:
            complement.validated = False
        elif validated in ["null"]:
            complement.validated = None
        elif validated:
            errors.append("validated invalido")

        if errors:
            return Response({"errors": errors},
                            status=status.HTTP_400_BAD_REQUEST)

        complement.save()

        return Response(status=status.HTTP_202_ACCEPTED)


class ComplementReportView(ListCreateRetrieveUpdateMix):
    queryset = CovidReport.objects.all()
    permission_classes = (ComplementPermission,)
    serializer_class = serializers.ComplementReportSerializer
    pagination_class = StandardResultsSetPagination
    action_serializers = {
        "create": serializers.ComplementReportSerializer,
        "update": serializers.ComplementReportSerializer,
        "list": serializers.ComplementReportSerializer,
    }

    def get_queryset(self):
        return CovidReport.objects.all().order_by("id")

    def update(self, request, **kwargs):
        self.check_permissions(request)
        complement = self.complement
        data = request.data
        data["key"] = ''
        serializer = self.get_serializer_class()(
            complement, data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            return Response(data, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response({"errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class CovidReportView2(ListCreateRetrieveUpdateMix):
    queryset = CovidReport.objects.all()
    permission_classes = (IsAdminOrCreateOnly,)
    #permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.CovidReportSerializer
    pagination_class = StandardResultsSetPagination
    action_serializers = {
        "create": serializers.CovidReportSimpleSerializer,
        "update": serializers.CovidReportSerializer,
        "list": serializers.CovidReportSerializer,
    }

    def get_queryset(self):
        return CovidReport.objects.all().order_by("id")

    def create(self, request, **kwargs):
        self.check_permissions(request)
        data_rep = request.data
        if data_rep.get('persona', False):
            persona_data = data_rep.pop('persona')
            pers = Persona()
            serializer_persona = serializers.PersonaSerializer(
                pers, data=persona_data)
            if serializer_persona.is_valid():
                persona = serializer_persona.save()
                data_rep["persona"] = persona.id
            else:
                return Response({"errors": serializer_persona.errors},
                                status=status.HTTP_400_BAD_REQUEST)

        new_covid_report = CovidReport()
        covid_report = None
        dosis_items = data_rep.pop('dosis', [])
        serializer_rep = self.get_serializer_class()(
            new_covid_report, data=data_rep)
        if serializer_rep.is_valid():
            covid_report = serializer_rep.save()
        else:
            print("Error en covid")
            return Response({"errors": serializer_rep.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        data_rep["covid_report"] = covid_report.id
        complement_rep = ComplementReport()
        print(data_rep)
        serializer_comp = serializers.ComplementReportSerializer(
            complement_rep, data=data_rep)
        if serializer_comp.is_valid():
            serializer_comp.save()
        else:
            print("Error en complement")
            return Response({"errors": serializer_comp.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        for dosis_item in dosis_items:
            dosis = DosisCovid()
            dosis.covid_report = covid_report
            serializer_dosis = serializers.DosisCovidListSerializer(
                dosis, data=dosis_item)
            if serializer_dosis.is_valid():
                serializer_dosis.save()
            else:
                print(serializer_dosis.errors)

        new_serializer = serializers.CovidReportSerializer(
            covid_report, context={'request': request})
        return Response(
            new_serializer.data, status=status.HTTP_201_CREATED)


class ReportList(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        
        clues = request.query_params.get("clues")
        state_inegi_code = request.query_params.get("estado")
        state_inegi_short_name = request.query_params.get("estado_nombre")
        institution_code = request.query_params.get("institucion")
        key = request.query_params.get("clave")
        validados = request.query_params.get("validados", "true")
        simple = request.query_params.get("simple", "false")
        selected_fields = request.query_params.get("fields", [])
        
        group_fields = {
            "hospital": {
                "finals": ["state", "institution", "clues", "hospital_name_raw"],
                "prefetch": ["state", "institution", "clues"],
            },
            "stories": {
                "finals": [
                    "testimony", "has_corruption", "narra_corrup"],
                "prefetch": ["complement"]
            },
            "supplies": {
                "finals": ["supplies"],
                "prefetch": [
                    "supplies", "supplies__component",
                    "supplies__presentation"]
            }
        }

        fields_included = ["id", "informer_type", "created"]
        prefetch_fields = []
        for group, fields in group_fields.items():
            #globals()[group] = False
            if group in selected_fields:
                #globals()[group] = True
                fields_included += fields["finals"]
                prefetch_fields += fields["prefetch"]
        
        report_query_filter = {}

        any_filter = any([clues, state_inegi_code, state_inegi_short_name,
                          institution_code, key])
            
        if clues:
            report_query_filter["clues__clues"] = clues
        if state_inegi_code:
            report_query_filter["state__inegi_code"] = state_inegi_code
        if state_inegi_short_name:
            report_query_filter["state__short_name"] = state_inegi_short_name
        if institution_code:
            report_query_filter["institution__code"] = institution_code

        if key:
            # Container.objects.filter(key=key)
            # Presentation.objects.filter(containers__key=key)
            # Component.objects.filter(presentations__containers__key=key)
            # Supply.objects.filter(component__presentations__containers__key=key)
            # Report.objects.filter(supplies__component__presentations__containers__key=key)
            report_query_filter[
                "supplies__component__"
                "presentations__containers__key"] = key

        if validados in ["yes"]:
            report_query_filter["validated"] = True
        elif validados in ["no"]:
            report_query_filter["validated"] = False
        elif validados in ["null"]:
            report_query_filter["validated"] = None
        elif validados in ["all"]:
            pass
        else:
            report_query_filter["validated"] = True

        if report_query_filter:
            report_query = Report.objects.filter(**report_query_filter)
        else:
            report_query = Report.objects.all()

        count = report_query.count()

        report_serializer = serializers.ReportApiSerializer
        print("prefetch_fields: ", prefetch_fields)
        print("fields_included: ", fields_included)
        serializer = report_serializer(
            report_query
            .prefetch_related(*prefetch_fields).order_by("created"),
            many=True, 
            context={"request": request, "fields_included": fields_included}
        )
        return Response({
            "count": count,
            "data": serializer.data
        })

        if simple in ["true"]:
            serializer = serializers.ReportPublicMinimSerializer(
                report_query
                    .prefetch_related("complement")
                    .order_by("created"),
                many=True
            )
        elif not any_filter or supplies in ["false"]:
            report_serializer = serializers.ReportPublicListSimpleSerializer
            serializer = report_serializer(
                report_query
                .prefetch_related(
                    "state",
                    "institution",
                    "complement",
                    "clues").order_by("created"),
                many=True
            )
        else:
            report_serializer = serializers.ReportPublicListSerializer
            serializer = report_serializer(
                report_query
                .prefetch_related(
                    "state",
                    "institution",
                    "clues",
                    "complement",
                    "supplies",
                    "supplies__component",
                    "supplies__presentation").order_by("created"),
                many=True
            )
        return Response({
            "count": count,
            "data": serializer.data
        })


class SupplyList2(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):

        validados = request.query_params.get("validados", "true")
        clues = request.query_params.get("clues")
        state_inegi_code = request.query_params.get("estado")
        state_inegi_short_name = request.query_params.get("estado_nombre")
        institution_code = request.query_params.get("institucion")
        key = request.query_params.get("clave")

        supply_query_filter = {}

        fields_included = ["id", "informer_type", "created"]
        any_filter = any([clues, state_inegi_code, state_inegi_short_name,
                          institution_code, key])
            
        if clues:
            supply_query_filter["report__clues__clues"] = clues
        if state_inegi_code:
            supply_query_filter["report__state__inegi_code"] = state_inegi_code
        if state_inegi_short_name:
            supply_query_filter["report__state__short_name"] = state_inegi_short_name
        if institution_code:
            supply_query_filter["report__institution__code"] = institution_code

        if validados in ["yes"]:
            supply_query_filter["report__validated"] = True
        elif validados in ["no"]:
            supply_query_filter["report__validated"] = False
        elif validados in ["null"]:
            supply_query_filter["report__validated"] = None
        elif validados in ["all"]:
            pass
        else:
            supply_query_filter["report__validated"] = True

        if supply_query_filter:
            supply_query = Supply.objects.filter(**supply_query_filter)
        else:
            supply_query = Supply.objects.all()

        count = supply_query.count()

        serializer = serializers.SupplyDisaggSerializer(
            supply_query
            .prefetch_related(
                "report", "report__complement", "component",
                "presentation", "disease")
            .order_by("report__created"),
            many=True, 
            context={"request": request, "fields_included": fields_included}
        )

        serializer_main = serializers.SupplyMainSerializer(
            supply_query
            .prefetch_related("report", "report__complement")
            .order_by("report__created"),
            many=True, 
            context={"request": request, "fields_included": fields_included}
        )
        return Response({
            "count": count,
            "data": serializer.data
        })


class TotalList(views.APIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request):
        from django.db.models import Count, F
        from django.db.models.functions import TruncMonth
        import math
        #from django.utils import timezone
        #from datetime import datetime
        #today = timezone.now()
        #date_time_str = "01/%s/%s" % (today.month, today.year)
        #date_time_obj = datetime.strptime(date_time_str, '%d/%m/%Y')
        print(date_time_obj)
        query_kwargs = {
            "report__complement__validated": True,
            "report__state__isnull": False,
            #"report__created__lt": date_time_obj,
            "report__institution__isnull": False,
        }
        values_group = ["report__state__short_name", "month",
                "report__state__inegi_code"]
        annotates = {
            "count": Count('id'),
            "mes": F('month'),
            "entidad_code": F('report__state__inegi_code'),
            "entidad": F('report__state__short_name'),
        }
        data = Supply.objects\
            .filter(**query_kwargs)\
            .annotate(month=TruncMonth('report__created'))\
            .values(*values_group)\
            .annotate(**annotates)\
            .values('entidad', 'mes', 'count', 'entidad_code')
        final_data = []
        for elem in data:
            month = elem["mes"].month
            elem["month"] = elem["mes"].month
            year = elem["mes"].year
            elem["year"] = year
            cuatri = math.floor((month-1) / 4) + 1
            elem["cuatri_number"] = cuatri
            cuatri_names = ["Ene-Abr", "May-Ago", "Sep-Dic"]
            year_last = str(year)
            elem["cuatrimestre"] = "%s %s" % (cuatri_names[cuatri-1], year_last[2:])
        return Response(data)
        #\ #.annotate(count=Count('id'))


class DinamicList(views.APIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, *args, **kwargs):
        from django.db.models import Count, F
        from django.db.models.functions import TruncMonth
        import math
        #from django.utils import timezone
        #from datetime import datetime
        #today = timezone.now()
        #date_time_str = "01/%s/%s" % (today.month, today.year)
        #date_time_obj = datetime.strptime(date_time_str, '%d/%m/%Y')
        group_name = kwargs.get("group_name")
        groups = {
            "total": {},
            "corruption": {
                "vals": ["has_corruption", "report__complement__has_corruption"],
            },
            "disease": {
                "filter": {"disease__isnull": False},
                "vals": ["padecimiento", "disease__name"],
            },
            "informer_type": {
                "filter": {"report__informer_type__isnull": False},
                "vals": ["informer_type", "report__informer_type"],
            },
            "medicine_type": {
                "filter": {"medicine_type__isnull": False},
                "vals": ["medicine_type", "medicine_type"],
            },
            "institution": {
                "vals": ["institucion", "report__institution__code"],
            },
        }
        group_params = groups[group_name]
        query_kwargs = {
            "report__complement__validated": True,
            "report__state__isnull": False,
            #"report__created__lt": date_time_obj,
            "report__institution__isnull": False,
        }
        values_group = [
            "report__state__short_name",
            "month",
            "report__state__inegi_code"
        ]
        annotates = {
            "count": Count('id'),
            "mes": F('month'),
            "entidad_code": F('report__state__inegi_code'),
            "entidad": F('report__state__short_name'),
        }
        display_vals = ['entidad', 'mes', 'count', 'entidad_code']
        
        vals = group_params.get("vals", None)
        final_groups = values_group + [vals[1]] if vals else values_group
        has_vals = vals and vals[0] != vals[1]
        compl_annotates = {vals[0]: F(vals[1])} if has_vals else {}        
        #compl_annotates = {vals[0]: F(vals[1])} if vals else {}
        final_display = display_vals + [vals[0]] if vals else display_vals
        data = Supply.objects\
            .filter(**{**query_kwargs, **group_params.get("filter", {})})\
            .annotate(month=TruncMonth('report__created'))\
            .values(*final_groups)\
            .annotate(**{**annotates, **compl_annotates})\
            .values(*final_display)
        #.values(*values_group+group_params.get("values", []))\
        #.annotate(**{**annotates, **group_params.get("annotates", {})})\
        #.values(*display_vals+group_params.get("display_vals", []))
        final_data = []
        cuatri_names = ["Ene-Abr", "May-Ago", "Sep-Dic"]
        for elem in data:
            month = elem["mes"].month
            elem["month"] = elem["mes"].month
            year = elem["mes"].year
            elem["year"] = year
            cuatri = math.floor((month-1) / 4) + 1
            elem["cuatri_number"] = cuatri
            year_str = str(year)
            elem["cuatrimestre"] = "%s %s" % (
                cuatri_names[cuatri-1], year_str[2:])
        return Response(data)


class RelatosList(views.APIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request):
        from django.db.models import Count, F, Q
        from django.db.models.functions import TruncMonth
        data = ComplementReport.objects\
            .filter(
                Q(testimony__isnull=False, validated=True) 
                    | Q(narration__isnull=False, validated=True))\
            .values('testimony', 'narration')\
            .annotate(
                testimonio=F('testimony'),
                narracion_corrupcion=F('narration')
            )\
            .values('testimonio', 'narracion_corrupcion')
        return Response(data)
        #\ #.annotate(count=Count('id'))


class ReportStateInstitutionCountList(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        from django.db.models import Count, F
        data = Supply.objects\
            .filter(report__complement__validated=True,
                    report__state__isnull=False,
                    report__institution__isnull=False)\
            .values("report__state", "report__institution")\
            .annotate(
                state=F('report__state'),
                institution=F('report__institution'),
                count=Count('id'))\
            .values('state', 'institution', 'count')
        return Response(data)
        #\ #.annotate(count=Count('id'))


class ReportExportView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from django.template.defaultfilters import slugify
        from wsgiref.util import FileWrapper
        from django.http import HttpResponse

        file_name = u"Exportación de Insumos y reportes %s" % timezone.now()\
            .strftime("%d-%m-%Y")
        slug_file_name = slugify(u"Exportación de Insumos y reportes")

        try:
            users_xlsx = open("%s.xlsx" % slug_file_name, 'rb')
        except Exception as e:
            return Response({"errors": [u"%s" % e]},
                            status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(FileWrapper(users_xlsx),
                                content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (
            "%s.xlsx" % file_name)
        return response


class ReportExportView2(GenericModelExport):
    queryset = Supply.objects.all()\
        .prefetch_related(
            "report",
            "report__state",
            "report__institution",
            "report__clues",
            "report__persona",
            "report__complement",
            "component",
            "component__group",
            "presentation",
            "disease")\
        .order_by("report__created", "id")
    permission_classes = [permissions.IsAdminUser]
    columns_width_pixel = True
    xlsx_name = u"Exportación de Insumos y reportes"
    tab_name = u"Listado"
    header_format = {'bold': True, "font_size": 13}
    data_config = [
        [u"id del Insumo", "id", 28],
        [u"Tipo de Medicina", "medicine_type", 134],
        [u"Grupo", "component.group.name", 160],
        [u"Componente", "component.name", 160],
        [u"Insumo faltante", "medicine_name_raw", 160],
        [u"Insumo (nombre real)", "medicine_real_name", 160],
        [u"Presentacion", "presentation.description", 160],
        [u"Presentacion escrita", "presentation_raw", 160],
        [u"id del Reporte", "report.id", 28],
        [u"Fecha de Registro", "report.created", 86],
        [u"Tipo de informante", "report.informer_type", 86],
        [u"Padecimiento (escrito)", "report.disease_raw", 154],
        [u"Padecimiento", "disease.name", 154],
        [u"Nombre de contacto", "report.persona.informer_name", 140],
        [u"Correo de contacto", "report.persona.email", 140],
        [u"Número de contacto", "report.persona.phone", 85],
        [u"Apoyo Litig", "report.persona.want_litigation", 40],
        [u"Apoyo Acomp", "report.persona.want_management", 40],
        [u"Edad", "report.age", 30],
        [u"Género", "report.gender", 30],
        [u"Entidad", "report.state.short_name", 120],
        [u"Institución (raw)", "report.institution_raw", 80],
        [u"Institución (s/CLUES)", "report.institution.public_name", 60],
        [u"Es otra institución", "report.is_other", 30],
        [u"CLUES", "report.clues.clues", 106],
        [u"Hospital o clínica", "report.get_clues_hospital_name", 240],
        [u"¿Hubo corrupción?", "report.complement.has_corruption", 40],
        [u"Relato de la corrupción", "report.complement.narration", 300],
        [u"Validado (por Nosotrxs)", "report.complement.validated", 30],
        [u"App", "report.complement.origin_app", 40],
        [u"Testimonio", "report.complement.testimony", 300],
    ]

    def get_file_name(self, request, **kwargs):
        return u"Exportación de Insumos y reportes"
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


class CovidReportExportView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from django.template.defaultfilters import slugify
        from wsgiref.util import FileWrapper
        from django.http import HttpResponse

        file_name = u"Exportación de Dosis y Reportes Covid %s" % timezone.now()\
            .strftime("%d-%m-%Y")
        slug_file_name = slugify(u"Exportación de Dosis y Reportes Covid")

        try:
            users_xlsx = open("%s.xlsx" % slug_file_name, 'rb')
        except Exception as e:
            return Response({"errors": [u"%s" % e]},
                            status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(FileWrapper(users_xlsx),
                                content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (
            "%s.xlsx" % file_name)
        return response


class CovidReportExportView2(GenericModelExport):
    queryset = DosisCovid.objects.all()\
        .prefetch_related(
            "state",
            "municipality",
            "covid_report",
            "covid_report__state",
            "covid_report__municipality",
            "covid_report__persona",
            "covid_report__complement")\
        .order_by("covid_report__created", "id")
    permission_classes = [permissions.IsAdminUser]
    columns_width_pixel = True
    xlsx_name = u"Exportación de Dosis y Reportes Covid"
    tab_name = u"Listado"
    header_format = {'bold': True, "font_size": 13}
    data_config = [
        [u"id de la Dosis", "id", 28],
        [u"Tipo de dosis", "get_type_success", 28],
        [u"Marca de la vacuna", "brand", 100],
        [u"Número de dosis", "round_dosis", 28],
        [u"Fecha de evento", "date", 35],
        [u"Razón de negativa", "reason_negative", 120],
        [u"Entidad negativa", "state.name", 120],
        [u"Municipio negativa", "state.short_name", 120],
        [u"Otra ubicación (neg)", "other_location", 40],
        [u"id del Reporte Covid", "covid_report.id", 28],
        [u"Fecha de Registro", "covid_report.created", 86],
        [u"Edad", "covid_report.age", 30],
        [u"Grupo Especial", "covid_report.special_group", 85],
        [u"Género", "covid_report.gender", 30],
        [u"Comorbilidades", "covid_report.comorbilities", 30],
        [u"Entidad residencia", "covid_report.state.short_name", 120],
        [u"Municipio residencia", "covid_report.municipality.name", 120],
        [u"Otra ubicación (residencia)", "covid_report.other_location", 120],
        [u"Nombre de contacto", "covid_report.persona.informer_name", 140],
        [u"Correo de contacto", "covid_report.persona.email", 140],
        [u"Número de contacto", "covid_report.persona.phone", 85],
        [u"Apoyo Litig", "report.persona.want_litigation", 40],        
        [u"¿Hubo corrupción?", "covid_report.complement.has_corruption", 40],
        [u"Relato de la corrupción", "covid_report.complement.narration", 300],
        [u"Validado (por Nosotrxs)", "covid_report.complement.validated", 30],
        [u"App", "covid_report.complement.origin_app", 40],
        [u"Testimonio", "covid_report.complement.testimony", 300],
    ]

    def get_file_name(self, request, **kwargs):
        return u"Exportación de Dosis y Reportes Covid"
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


class PublicReportExportView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.utils import timezone
        from django.template.defaultfilters import slugify
        from wsgiref.util import FileWrapper
        from django.http import HttpResponse

        file_name = u"Exportación pública de reportes %s" % timezone.now()\
            .strftime("%d-%m-%Y")
        slug_file_name = slugify(u"Exportación de Insumos y reportes público")

        try:
            users_xlsx = open("%s.xlsx" % slug_file_name, 'rb')
        except Exception as e:
            return Response({"errors": [u"%s" % e]},
                            status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(FileWrapper(users_xlsx),
                                content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (
            "%s.xlsx" % file_name)
        return response


class PublicReportExportView2(GenericModelExport):
    queryset = Supply.objects.filter(report__validated=True)\
        .prefetch_related(
            "report",
            "report__state",
            "report__institution",
            "report__clues",
            "report__complement",
            "component",
            "component__group",
            "presentation",
            "disease")\
        .order_by("report__created", "id")


    permission_classes = [permissions.AllowAny]
    columns_width_pixel = True
    xlsx_name = u"Exportación de Insumos y reportes"
    tab_name = u"Registros históricos"
    header_format = {'bold': True, "font_size": 13}
    data_config = [
        [u"id del Insumo", "id", 28],
        [u"Tipo de Medicina", "medicine_type", 134],
        [u"Grupo", "component.group.name", 160],
        [u"Componente", "component.name", 160],
        [u"Presentacion", "presentation.description", 160],
        [u"id del Reporte", "report.id", 28],
        [u"Fecha de Registro", "report.created", 86],
        [u"Tipo de informante", "report.informer_type", 86],
        [u"Padecimiento", "disease.name", 154],
        [u"Entidad", "report.state.short_name", 120],
        [u"Institución", "report.institution.public_name", 60],
        [u"Institución 2", "report.hospital_name_raw", 80],
        [u"CLUES", "report.clues.clues", 106],
        [u"Hospital o clínica", "report.get_clues_hospital_name", 240],
    ]

    def get_file_name(self, request, **kwargs):
        return u"Exportación pública de Insumos y reportes"
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


class ReportMedicineView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from desabasto.models import Supply
        from django.db.models import Q
        q = request.query_params.get("q")
        if not q:
            raise ValidationError({"errors": [
                "se deve mandar el parametro q, "
                "puede ser una lista separada por comas"]})
        q = [element.strip() for element in q.split(",") if element.strip()]
        title = q[0]
        reports = []
        first_q = q.pop(0)
        q_query = Q(
            medicine_name_raw__icontains=first_q) | Q(
            medicine_real_name__icontains=first_q)
        for q_word in q:
            q_query |= Q(medicine_name_raw__icontains=q_word)
            q_query |= Q(medicine_real_name__icontains=q_word)
        #
        for supply in Supply.objects.filter(q_query).distinct():
            container = getattr(supply, "container", None)
            presentation = getattr(container, "presentation", None)
            presentation_type_raw = getattr(
                presentation, "presentation_type_raw", None)
            institution = getattr(supply.report, "institution")
            state = getattr(supply.report, "state")
            if state:
                state_name = state.short_name or state.code_name or state.name
            else:
                state_name = None
            data = {
                "key": getattr(container, "key", None),
                "container_name": getattr(container, "name", None),
                "presentation_type_raw": presentation_type_raw,
                "created": supply.report.created.strftime("%Y/%m/%d"),
                "institution": getattr(institution, "code", None),
                "state": state_name,
            }
            reports.append(data)
        return Response({
            "name": title,
            "reports_count": len(reports),
            "reports": reports},
            status=status.HTTP_200_OK)
