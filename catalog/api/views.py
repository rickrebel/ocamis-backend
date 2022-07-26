# -*- coding: utf-8 -*-
from . import serializers
from rest_framework import permissions, views, status

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)
from desabasto.api.views import StandardResultsSetPagination

from catalog.models import Institution, State, CLUES, Entity
from rest_framework.response import Response


class StateViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.StateListSerializer
    queryset = State.objects.all()
    action_serializers = {
        "list": serializers.StateListSerializer,
        "retrieve": serializers.StateSerializer,
    }


class EntityViewSet(ListRetrieveUpdateMix):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.EntitySerializer
    queryset = Entity.objects.all().prefetch_related(
            "petitions",
            "petitions__petition_months",
            "petitions__file_groups",
            "petitions__file_groups__group_file",
            "petitions__file_groups__group_file__group_data",
            "petitions__file_groups__group_file__type_file",
            "petitions__file_groups__group_file__group_tranformations",
            "petitions__file_groups__group_file__group_tranformations__clean_function",
            "petitions__file_groups__data_files",
            "petitions__file_groups__data_files__status_process",
            "petitions__file_groups__data_files__month_entity",
        )
    
    action_serializers = {
        "list": serializers.EntitySerializer,
        "retrieve": serializers.EntityFullSerializer,
    }

    def get(self, request):
        print("ESTOY EN GET")
        entity = self.get_object()
        serializer = serializers.EntityFullSerializer(
            entity, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()

    """ @action(methods=["post"], detail=True, url_path='create_months')
    def create_months(self, request, **kwargs):
        import json
        from files_rows.models import MonthEntity
        if not request.user.is_staff:
            raise PermissionDenied()
        limiters = request.data.get("limiters")
        limiters = json.loads(limiters)
        entity = self.get_object()
        
        MonthEntity.objects.create()
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

        return Response(status=status.HTTP_202_ACCEPTED)"""


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
