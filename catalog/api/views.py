# -*- coding: utf-8 -*-
from . import serializers
from rest_framework import permissions, views, status

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix)
from desabasto.api.views import StandardResultsSetPagination

from catalog.models import Institution, State, CLUES, Entity
from rest_framework.response import Response
from rest_framework.decorators import action


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
            "petitions__file_controls",
            "petitions__break_dates",
            "petitions__negative_reasons",
            "petitions__negative_reasons__negative_reason",
            "petitions__file_controls",
            #"petitions__file_controls__file_control",
            #"petitions__file_controls__file_control__data_group",
            #"petitions__file_controls__file_control__file_type",
            #"petitions__file_controls__file_control__file_tranformations",
            #"petitions__file_controls__file_control__file_tranformations__clean_function",
            #"petitions__file_controls__data_files",
            #"petitions__file_controls__data_files__status_process",
            #"petitions__file_controls__data_files__month_entity",
        )
    
    action_serializers = {
        "list": serializers.EntitySerializer,
        "retrieve": serializers.EntityFullSerializer,
        "update": serializers.EntitySerializer,
        "data_viz": serializers.EntityVizSerializer,
    }

    def get(self, request):
        print("ESTOY EN GET")
        entity = self.get_object()
        serializer = serializers.EntityFullSerializer(
            entity, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path='create_months')
    def create_months(self, request, **kwargs):
        import json
        from inai.models import MonthEntity
        if not request.user.is_staff:
            raise PermissionDenied()
        year = request.data.get("year")
        entity = self.get_object()
        for month in range(12):
            try:
                month += 1
                ye_mo = "%s%s%s" % (year, '0' if month < 10 else '', month)
                MonthEntity.objects.create(entity=entity, year_month=ye_mo)
            except Exception as e:
                return Response(
                    {"errors": ["No se pudo crear", "%s" % e]},
                    status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_202_ACCEPTED)
    
    @action(methods=["get"], detail=False, url_path='data_viz')
    def data_viz(self, request, **kwargs):
        #import json
        from catalog.api.final_viz import (
            fetch_entities, build_quality_simple)
        from category.models import TransparencyIndex, TransparencyLevel
        from category.api.serializers import (
            TransparencyIndexSerializer, TransparencyLevelSimpleSerializer)
        from inai.models import FileControl
        from inai.api.serializers import FileControlSimpleSerializer
        from inai.api.serializers_viz import (
            FileControlViz2Serializer)
        indices_query = TransparencyIndex.objects.all()\
            .prefetch_related(
                "levels", "levels__anomalies", "levels__file_formats")
        indices = TransparencyIndexSerializer(indices_query, many=True).data
        #operability = indices_query.filter(short_name="operability").first()
        #operability_levels = operability.levels.all()
        operb_levels_query = TransparencyLevel.objects\
            .filter(transparency_index__short_name="operability")\
            .prefetch_related("anomalies", "file_formats")\
            .order_by("value")
        operability_levels = TransparencyLevelSimpleSerializer(
            operb_levels_query, many=True).data

        pilot = request.query_params.get("is_pilot", "false")
        is_pilot = pilot.lower() in ["si", "yes", "true"]
        include_groups = ["detailed", "stock"]
        all_entities = fetch_entities(include_groups)
        if is_pilot:
            all_entities = all_entities.filter(is_pilot=True)

        serializer = self.get_serializer_class()(
            all_entities, many=True, context={'request': request})
        detailed_controls_query = FileControl.objects\
            .filter(
                data_group__name="detailed",
                petition_file_control__isnull=False
            )\
            .prefetch_related(
                "anomalies",
                "columns__final_field",
                "columns__final_field__collection",
                "petition_file_control__petition__entity"
            )\
            .distinct()
        #detailed_controls_query
        #detailed_controls = {}
        #detailed_controls = FileControlSimpleSerializer(
        detailed_controls = FileControlViz2Serializer(
            detailed_controls_query, many=True).data
        for file_ctrl in detailed_controls:
            anomalies = set(file_ctrl["anomalies"])
            file_formats = set([file_ctrl["file_format"]])
            final_operatib = "other_oper"
            #print(file_formats)
            for level in operability_levels:
                if not set(level["file_formats"]).isdisjoint(file_formats):
                    final_operatib = level["short_name"]
                if not set(level["anomalies"]).isdisjoint(anomalies):
                    final_operatib = level["short_name"]
                #for other_cond in level["other_conditions"]:
                #    if locals()[other_cond]:
                #        final_operatib = leved["short_name"]
            file_ctrl["operability_name"] = final_operatib
            try:
                file_ctrl["has_ent_clues"] = bool(
                    file_ctrl["petition_file_control"][0])
            except:
                file_ctrl["has_ent_clues"] = False
            #clues, formula, droug = build_quality_simple(file_ctrl)
            file_ctrl["quality_names"] = build_quality_simple(file_ctrl)
            file_ctrl["entity"] = file_ctrl["entities"][0]
            #file_ctrl["quality_names"] = {}
            #file_ctrl["quality_names"]["clues"] = clues
            #file_ctrl["quality_names"]["formula"] = formula
            #file_ctrl["quality_names"]["droug"] = droug
            #all_comps = [clues, formula, droug]
            final_qual = "not_enough"
            quality_levels = ["enough", "almost_enough", "not_enough"]
            for qual_level in quality_levels:
                #if qual_level in all_comps:
                if qual_level in file_ctrl["quality_names"].values():
                    final_qual = qual_level
            file_ctrl["quality_names"]["final"] = final_qual
        #detailed_controls

        #.filter(petition_file_control="detailed")\

        status_negative = [ "negative_response"]
        status_delivered = ["with_data", "partial_data"]
        status_other = ["waiting", "pick_up",]
        #enoughs = ["not_enough", "enough", "almost_enough", "not_enough"]
        final_data = {"file_controls": detailed_controls}
        final_data["entities"] = []
        for entity in serializer.data:
            #entity["file_ctrls"] = [ctrl for ctrl in detailed_controls 
            #    if ctrl["entity"] and entity["id"]]
            for petition in entity["petitions"]:
                status_data = petition["status_data"]
                if not status_data or status_data in status_negative:
                    petition["access_name"] = "negative"
                elif status_data == "no_response":
                    petition["access_name"] = "no_response"
                elif status_data in status_delivered:
                    petition["access_name"] = "delivered"
                elif status_data in status_other:
                    petition["access_name"] = "other_access"
                else:
                    petition["access_name"] = "other_access"
                many_ctrls = len(petition["file_controls"]) > 1
                petition["many_file_controls"] = many_ctrls

            final_data["entities"].append(entity)

        #return Response(
        #    serializer.data, status=status.HTTP_200_OK)
        return Response(final_data, status=status.HTTP_200_OK)


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
