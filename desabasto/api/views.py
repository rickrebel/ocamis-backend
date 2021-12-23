# -*- coding: utf-8 -*-
from xlsx_export.generic import GenericModelExport
from . import serializers
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotFound, PermissionDenied, ValidationError)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from django.db.models import Q

from desabasto.models import (
    State, Report, Institution, CLUES, Supply, Component,
    Group, PresentationType, Presentation, Container, Alliances, Disease)

from api.mixins import ListMix
from api.mixins import MultiSerializerListRetrieveMix
from api.mixins import (MultiSerializerListCreateRetrieveUpdateMix as
                        ListCreateRetrieveUpdateMix)

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


class StateList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.StateListSerializer
    queryset = State.objects.all()


class InstitutionList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.InstitutionListSerializer
    queryset = Institution.objects.all().order_by("relevance")
    # pagination_class = StandardResultsSetPagination


class CLUESList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.CLUESListSerializer
    queryset = CLUES.objects.filter(is_searchable=True)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qset = CLUES.objects.filter(is_searchable=True)\
            .order_by('-total_unities')
        institution = str(self.request.query_params.get("institution"))
        state = str(self.request.query_params.get("state"))
        if institution.isdigit():
            if institution == "0":
                qset = qset.filter(institution__relevance__gte=2)
            else:
                qset = qset.filter(institution__id=institution)
        if state.isdigit():
            qset = qset.filter(state__id=state)
        return qset.distinct()


class SupplyList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.SupplyListSerializer
    queryset = Supply.objects.all()
    pagination_class = StandardResultsSetPagination


class IsAdminOrCreateOnly(BasePermission):

    def has_permission(self, request, view):
        if view.action == 'create':
            return True
        else:
            return request.user.is_staff


class ReportView(ListCreateRetrieveUpdateMix):
    permission_classes = (IsAdminOrCreateOnly,)
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

    @action(methods=["post"], detail=True, url_path='pending')
    def pending(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        pending = request.data.get("pending")
        validated = request.data.get("validated")
        report = self.get_object()
        errors = []

        if pending in [True, "true"]:
            report.pending = True
        elif pending in [False, "false"]:
            report.pending = False
        elif pending:
            errors.append("pending invalido")

        if validated in [True, "true"]:
            report.validated = True
        elif validated in [False, "false"]:
            report.validated = False
        elif validated in ["null"]:
            report.validated = None
        elif validated:
            errors.append("validated invalido")

        if errors:
            return Response({"errors": errors},
                            status=status.HTTP_400_BAD_REQUEST)

        report.save()

        return Response(status=status.HTTP_202_ACCEPTED)


class ReportList(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        clues = request.query_params.get("clues")
        state_inegi_code = request.query_params.get("estado")
        state_inegi_short_name = request.query_params.get("estado_nombre")
        institution_code = request.query_params.get("institucion")
        key = request.query_params.get("clave")
        validados = request.query_params.get("validados", "yes")
        supplies = request.query_params.get("supplies", "true")
        report_query_filter = {}

        any_filter = any([clues, state_inegi_code, state_inegi_short_name,
                          institution_code, key])
        if not any_filter:
            return Response({
                "count": 0,
                "data": [],
                "warnings": ["requiere almenos uno de los filtros"]
            })

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
        else:
            # all, omision, error u otros
            pass

        if report_query_filter:
            report_query = Report.objects.filter(**report_query_filter)
        else:
            report_query = Report.objects.all()

        count = report_query.count()

        if supplies in ["false"]:
            report_serializer = serializers.ReportPublicListSimpleSerializer
        else:
            report_serializer = serializers.ReportPublicListSerializer

        serializer = report_serializer(
            report_query
            .prefetch_related(
                "state",
                "institution",
                "clues",
                "supplies",
                "supplies__component",
                "supplies__presentation").order_by("created"),
            many=True
        )
        return Response({
            "count": count,
            "data": serializer.data
        })


class ReportStateInstitutionCountList(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        from django.db.models import Count
        data = Report.objects\
            .filter(validated=True, state__isnull=False,
                    institution__isnull=False)\
            .values("state", "institution").annotate(count=Count('id'))
        return Response(data)


class CatalogView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        data = {
            "states": serializers.StateSerializer(
                State.objects.all(), many=True).data,
            "institutions": serializers.InstitutionSerializer(
                Institution.objects.all().order_by("relevance"),
                many=True).data,
            "alliances": serializers.AlliancesSerializer(
                Alliances.objects.all().order_by("name"),
                many=True, context={"request": request}).data,
            "diseases": serializers.DiseaseSerializer(
                Disease.objects.all().order_by("name"),
                many=True, context={"request": request}).data
        }
        return Response(data)


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
    queryset = Supply.objects.all().order_by("report__created", "id")
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
        [u"Trimestre", "report.trimester", 86],
        [u"Tipo de informante", "report.informer_type", 86],
        [u"Padecimiento (escrito)", "report.disease_raw", 154],
        [u"Padecimiento", "disease.name", 154],
        [u"Nombre de contacto", "report.informer_name", 140],
        [u"Correo de contacto", "report.email", 140],
        [u"Número de contacto", "report.phone", 85],
        [u"Edad", "report.age", 30],
        [u"Entidad", "report.state.short_name", 120],
        [u"Institución (raw)", "report.institution_raw", 80],
        [u"Institución (s/CLUES)", "report.institution.public_name", 60],
        [u"Es otra institución", "report.is_other", 30],
        [u"CLUES", "report.clues.clues", 106],
        [u"Hospital o clínica", "report.get_clues_hospital_name", 240],
        [u"¿Hubo corrupción?", "report.has_corruption", 40],
        [u"Relato de la corrupción", "report.narration", 300],
        [u"Validado (por Nosotrxs)", "report.validated", 30],
        [u"App", "report.origin_app", 40],
    ]

    def get_file_name(self, request, **kwargs):
        return u"Exportación de Insumos y reportes"
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
        .order_by("report__created", "id")
    permission_classes = [permissions.AllowAny]
    columns_width_pixel = True
    xlsx_name = u"Exportación de Insumos y reportes"
    tab_name = u"Registros históricos"
    header_format = {'bold': True, "font_size": 13}
    data_config = [
        [u"Fecha de Registro", "report.created", 86],
        [u"Trimestre", "report.trimester", 86],
        [u"Tipo de Medicina", "medicine_type", 134],
        [u"Insumo (nombre real)", "medicine_real_name", 160],
        [u"Padecimiento (escrito)", "report.disease_raw", 154],
        [u"Padecimiento final", "disease.name", 154],
        [u"Entidad", "report.state.short_name", 120],
        [u"Institución (s/CLUES)", "report.get_institution_name", 60],
        [u"Institución 2", "report.hospital_name_raw", 80],
        [u"Clave CLUES", "report.clues.clues", 106],
        [u"Hospital o clínica", "report.get_clues_hospital_name", 240],
        [u"Tipo de informante", "report.informer_type", 86],
        [u"Componente", "component.name", 40],
        [u"Presentacion", "presentation.description", 40],
    ]

    def get_file_name(self, request, **kwargs):
        return u"Exportación de Insumos y reportes público"
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


class ComponentList(MultiSerializerListRetrieveMix):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ComponentSerializer
    queryset = Component.objects.all()
    action_serializers = {
        "retrieve": serializers.ComponentRetrieveSerializer,
    }

    def list(self, request):
        from django.db.models import Q
        q = request.query_params.get("q")
        if q:
            q_list = [word.strip() for word in q.split(",") if word]
        else:
            q_list = None

        if q_list:

            first_word = q_list.pop()
            query_and = Q(name__icontains=first_word,
                          alias__icontains=first_word)
            query_or = Q(Q(name__icontains=first_word) |
                         Q(alias__icontains=first_word))
            for word in q_list:
                query_and |= Q(name__icontains=word,
                               alias__icontains=word)
                query_or |= Q(Q(name__icontains=word) |
                              Q(alias__icontains=word))

            queryset = Component.objects.filter(is_relevant=True)\
                .filter(query_and).distinct()

            if queryset.count() < 200:
                queryset_2 = Component.objects.filter(is_relevant=False)\
                    .filter(query_and).distinct()
                queryset = queryset.union(queryset_2)

            if queryset.count() < 200:
                queryset_3 = Component.objects.filter(is_relevant=True)\
                    .filter(query_or).distinct()
                queryset = queryset.union(queryset_3)

            if queryset.count() < 200:
                queryset_4 = Component.objects.filter(is_relevant=False)\
                    .filter(query_or).distinct()
                queryset = queryset.union(queryset_4)
        else:
            queryset = Component.objects.all()

        serializer = self.get_serializer_class()(
            # queryset.distinct()[:200], many=True)
            queryset.distinct().order_by("-frequency"), many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='key')
    def key(self, request, **kwargs):
        clave = request.query_params.get("clave")
        try:
            container = Container.objects.get(key=clave)
        except Container.DoesNotExist:
            raise NotFound({"errors": "No se encontro la clave: %s" % clave})
        serializer = serializers.ComponentRetrieveSerializer(
            container.presentation.component)
        return Response(serializer.data)


class GroupList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.GroupSerializer
    queryset = Group.objects.all()
    pagination_class = StandardResultsSetPagination


class PresentationTypeList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PresentationTypeSerializer
    queryset = PresentationType.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(name__icontains=q) |
            Q(common_name__icontains=q) |
            Q(alias__icontains=q)
        ).distinct()


class PresentationList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PresentationSerializer
    queryset = Presentation.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(component__name__icontains=q) |
            Q(component__alias__icontains=q) |
            Q(component__presentations_raw__icontains=q) |
            Q(presentation_type__name__icontains=q) |
            Q(presentation_type__common_name__icontains=q) |
            Q(presentation_type__alias__icontains=q) |
            Q(description__icontains=q) |
            Q(presentation_type_raw__icontains=q) |
            Q(clave__icontains=q) |
            Q(official_name__icontains=q) |
            Q(official_attributes__icontains=q) |
            Q(short_attributes__icontains=q)
        ).distinct()


class ContainerList(ListMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.ContainerSerializer
    queryset = Container.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        q = self.request.query_params.get(
            "q", self.request.query_params.get("filter"))
        return self.queryset.filter(
            Q(name__icontains=q) |
            Q(key__icontains=q) |
            Q(short_name__icontains=q)
        ).distinct()


class SendEmailNewOrganizationView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from email_sendgrid.models import (
            TemplateBase, EmailRecord, SendGridProfile)

        sendgrid_nosotrxs = SendGridProfile.objects\
            .filter(name="Nosotrxs").first()

        try:
            template = TemplateBase.objects.get(
                name="new_organization")
        except Exception as e:
            return Response(
                {"errors": ["template no registrado", u"%s" % e]},
                status=status.HTTP_400_BAD_REQUEST)

        email = "andres.castaneda@nosotrxs.org"
        data = request.data
        email_register = EmailRecord()
        email_register.send_email = True
        email_register.email = email
        email_register.sendgrid_profile = sendgrid_nosotrxs
        email_register.template_base = template
        email_register.type_message = "New Organization"
        email_register.save(user_data=data)
        if not email_register.x_message_id:
            return Response({"errors": ["no se pudo mandar el correo"]},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


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
