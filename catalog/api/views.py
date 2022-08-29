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
        return Response()

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
        from django.db.models import Prefetch
        from inai.models import NameColumn, Petition, FileControl
        operability = {
            "ideal": {
                "formats": ["csv", "json", "txt"],
                "anomalies": [],
                "others": [],
            },
            "aceptable": {
                "formats": ["xls"],
                "anomalies": [
                    "code_headers",
                    "no_headers",
                    "hide_colums_tabs"
                ],
                "others": [],
            },
            "enhaced": {
                "formats": [],
                "anomalies": [
                    "different_tipe_tabs",
                    "internal_catalogue",
                    "hide_colums_tabs",
                    "no_valid_row_data",
                    "concatenated"
                    "same_group_data",
                    #solo para local:
                    "abasdf",
                ],
                "others": ["many_file_controls"],
            },
            "impeachable": {
                "formats": ["pdf", "word", "email", "other"],
                "anomalies": ["row_spaces"],
                "others": [],
            },
        }        
        qualities = ["not_enough", "enough", "almost_enough", "not_enough"]

        pilot = request.query_params.get("is_pilot", "false")
        is_pilot = pilot.lower() in ["si", "yes", "true"]
        filter_columns = NameColumn.objects.filter(
            final_field__isnull=False, final_field__need_for_viz=True)
        prefetch_columns = Prefetch(
            "petitions__file_controls__file_control__columns", 
            queryset=filter_columns)
        filter_petitions = Petition.objects\
            .exclude(status_petition__name="mistake", )
        prefetch_petitions = Prefetch("petitions", queryset=filter_petitions)
        include_groups = ["detailed", "stock"]
        filter_file_control = FileControl.objects\
            .filter(data_group__name__in=include_groups)
        prefetch_file_control = Prefetch(
            "petitions__file_controls__file_control",
            queryset=filter_file_control)
        all_entities = Entity.objects\
            .filter(competent=True, vigencia=True)\
            .prefetch_related(
                "institution",
                "clues",
                "state",
                #"petitions",
                prefetch_petitions,
                "petitions__status_data",
                "petitions__status_petition",
                "petitions__petition_months",
                "petitions__petition_months__month_entity",
                prefetch_file_control,
                "petitions__file_controls__file_control__data_group",
                prefetch_columns,
                "petitions__file_controls__file_control__columns__final_field",
                "petitions__file_controls__file_control__columns__final_field__collection",
            )
        if is_pilot:
            all_entities = all_entities.filter(is_pilot=True)

        serializer = self.get_serializer_class()(
            all_entities, many=True, context={'request': request})

        final_data = []
        status_no_data = ["no_data", "waiting", "pick_up"]
        for entity in serializer.data:
            for petition in entity["petitions"]:
                status_data = petition["status_data"]
                for data_group in include_groups:
                    file_ctrls = [
                        file_ctrl for file_ctrl in petition["file_controls"]
                        if file_ctrl["data_group"]["name"] == data_group]
                    file_formats = [
                        file_ctrl["format_file"] for file_ctrl in file_ctrls]
                    anomalies = []
                    for file_ctrl in file_ctrls:
                        anomalies += file_ctrl["anomalies"]
                    file_ctrls_count = len(file_ctrls)
                    many_file_controls = file_ctrls_count > 1
                    final_quality = None
                    for (curr_quality, params) in operability.items():
                        if not set(params["formats"]).isdisjoint(set(file_formats)):
                            final_quality = curr_quality
                        if not set(params["anomalies"]).isdisjoint(set(anomalies)):
                            final_quality = curr_quality
                        for other in params["others"]:
                            if locals()[other]:
                                final_quality = curr_quality
                    if not status_data or status_data["name"] in status_no_data:
                        final_quality = "no_data"
                    petition[data_group] = {
                        "file_formats": file_formats,
                        "many_file_controls": many_file_controls,
                        "quality": final_quality,
                        "file_ctrls_count": file_ctrls_count,
                    }

                    if data_group != "detailed":
                        continue
                    clues = 0
                    formula = 0
                    droug = 0
                    for file_ctrl in file_ctrls:
                        final_fields = file_ctrl["columns"]
                        has_clues = ("CLUES", "clues") in final_fields
                        has_name = ("CLUES", "name") in final_fields
                        if has_clues and clues < 2:
                            clues = 1
                        elif (has_clues or has_name) and clues < 3:
                            clues = 2
                        else:
                            clues = 3
                        emision = (("Prescription", "fecha_emision") in final_fields or
                            ("Prescription", "fecha_consulta") in final_fields)
                        entrega = ("Prescription", "fecha_entrega") in final_fields
                        folio = ("Prescription", "folio_documento") in final_fields
                        if folio and emision and entrega and formula < 2:
                            formula = 1
                        elif folio and (emision or entrega) and formula < 3:
                            formula = 2
                        else:
                            formula = 3
                        official_key = ("Container", "key2") in final_fields
                        prescrita = ("Droug", "cantidad_prescrita") in final_fields
                        entregada = ("Droug", "cantidad_entregada") in final_fields
                        own_key = ("Container", "_own_key") in final_fields
                        other_names = (("Droug", "droug_name") in final_fields or
                            ("Presentation", "description") in final_fields or
                            ("Container", "name") in final_fields)
                        if prescrita and entregada:
                            if official_key and droug < 2:
                                droug = 1
                            elif (official_key or other_names or own_key) and droug < 3:
                                droug = 2
                        if not droug:
                            droug = 3
                    if not status_data or status_data["name"] in status_no_data:
                        petition[data_group]["clues"] = "no_data"
                        petition[data_group]["formula"] = "no_data"
                        petition[data_group]["droug"] = "no_data"
                    else:
                        petition[data_group]["clues"] = qualities[clues]
                        petition[data_group]["formula"] = qualities[formula]
                        petition[data_group]["droug"] = qualities[droug]

            final_data.append(entity)

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
