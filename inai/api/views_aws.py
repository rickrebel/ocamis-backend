# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
import unidecode

from inai.models import DataFile, NameColumn, Petition, PetitionFileControl

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,
    MultiSerializerListRetrieveMix as ListRetrieveView)

from rest_framework.exceptions import (PermissionDenied, ValidationError)
from catalog.api.serializers import EntityFileControlsSerializer


class AutoExplorePetitionViewSet(ListRetrieveView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "retrieve": serializers.PetitionFullSerializer,
    }

    def retrieve(self, request, pk=None):
        #self.check_permissions(request)
        import zipfile
        import rarfile
        import pathlib
        from django.conf import settings
        from inai.models import ProcessFile, FileControl
        from category.models import FileType
        from data_param.models import DataGroup
        from io import BytesIO
        from scripts.common import get_file, start_session, create_file

        is_prod = getattr(settings, "IS_PRODUCTION", False)
        all_errors = []

        s3_client = None
        dev_resource = None
        if is_prod:
            s3_client, dev_resource = start_session()

        petition = self.get_object()
        current_file_ctrl = request.query_params.get("file_ctrl", False)

        process_files = ProcessFile.objects.filter(
            petition=petition, has_data=True)
        data_group = DataGroup.objects.get(name="orphan")
        file_type = FileType.objects.get(name="with_data")
        name_control = "Archivos por agrupar. Petición %s" % (
            petition.folio_petition)
        prev_file_controls = FileControl.objects.filter(data_group=data_group, 
            petition_file_control__petition=petition)
        if prev_file_controls.exists():
            file_control = prev_file_controls.first()
        else:
            file_control, created = FileControl.objects.get_or_create(
                name=name_control,
                file_type=file_type,
                data_group=data_group,
                final_data=False,
                )
        pet_file_ctrl, created_pfc = PetitionFileControl.objects\
            .get_or_create(
                file_control=file_control, petition=petition)

        process_file_ids = []
        
        for process_file in process_files:
            process_file_ids.append(process_file.id)
            if DataFile.objects.filter(process_file=process_file).exists():
                continue
            suffixes = pathlib.Path(process_file.final_path).suffixes
            suffixes = set([suffix.lower() for suffix in suffixes])
            if is_prod:
                bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
                zip_obj = dev_resource.Object(
                    bucket_name=bucket_name, 
                    key=f"{settings.AWS_LOCATION}/{process_file.file.name}"
                    )
                buffer = BytesIO(zip_obj.get()["Body"].read())
            else:
                buffer = get_file(process_file, dev_resource)
            # RICK AWS corroborar si en necesario
            #if is_prod:
            #    buffer = BytesIO(buffer.read())
            
            if '.zip' in suffixes:
                zip_file = zipfile.ZipFile(buffer) 
            elif '.rar' in suffixes:
                zip_file = rarfile.RarFile(buffer)
            else:
                continue

            for zip_elem in zip_file.infolist():
                if zip_elem.is_dir():
                    continue
                pos_slash = zip_elem.filename.rfind("/")
                only_name = zip_elem.filename[pos_slash + 1:]
                directory = (zip_elem.filename[:pos_slash]
                    if pos_slash > 0 else None)
                #z_file.open(filename).read()
                file_bytes = zip_file.open(zip_elem).read()

                curr_file, file_errors = create_file(
                    process_file, file_bytes, only_name, s3_client=s3_client)
                if file_errors:
                    all_errors += file_errors
                    continue

                new_file = DataFile.objects.create(
                    file=curr_file,
                    process_file=process_file,
                    directory=directory,
                    #status_process=initial_status,
                    petition_file_control=pet_file_ctrl,
                    )
                new_file.change_status('initial')

        all_data_files = DataFile.objects.filter(
            petition_file_control=pet_file_ctrl).order_by("date")

        last_file_control = None
        entity_file_controls = FileControl.objects.filter(
            petition_file_control__petition__entity=petition.entity,
            file_format__isnull=False)\
            .exclude(data_group__name="orphan")\
            .prefetch_related("columns")\
            .distinct()

        if current_file_ctrl:
            entity_file_controls = entity_file_controls.filter(
                id=current_file_ctrl)

        near_file_controls = entity_file_controls.filter(
            petition_file_control__petition=petition)
        others_file_controls = entity_file_controls.exclude(
            petition_file_control__petition=petition)

        all_file_controls = near_file_controls | others_file_controls
        for data_file in all_data_files:
            saved = False
            data_file.error_process = []
            #print("data_file_original: ", data_file)
            data_file.save()
            data_file, errors, suffix = data_file.decompress_file()
            if not data_file:
                print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
                continue
            for file_ctrl in all_file_controls:
                saved = data_file.find_coincidences(
                    file_ctrl, suffix, saved, petition)
                #print(f"Vamos por file control {file_ctrl.name}")
                #data_file.explore_data = validated_data
                #data_file.save()
            if not saved:
                data_file.change_status("explore_fail")
        
        petition_data = serializers.PetitionFullSerializer(petition).data
        data = {
            "errors": all_errors,
            "petition": petition_data,
            "file_controls": EntityFileControlsSerializer(
                petition.entity).data["file_controls"],
        }
        return Response(data, status=status.HTTP_200_OK)


def move_and_duplicate(data_files, petition, request):
    from rest_framework.exceptions import ParseError
    from inai.models import ProcessFile, FileControl
    from category.models import FileType #, StatusControl

    destination = request.data.get("destination")
    is_dupl = request.data.get("duplicate")
    #initial_status = StatusControl.objects.get(
    #    name="initial", group="process")
    errors = []
    if destination == "process_file":
        file_type_no_final = FileType.objects.get(name="no_final_info")
        for data_file in data_files:
            ProcessFile.objects.create(
                petition=petition,
                file=data_file.file,
                file_type=file_type_no_final)
            if not is_dupl:
                data_file.delete()
    elif destination:
        file_ctrl_id = int(destination)
        pet_file_ctrls = PetitionFileControl.objects.filter(
            petition=petition, file_control_id=file_ctrl_id)
        if pet_file_ctrls.exists():
            pet_file_ctrl = pet_file_ctrls.first()
        else:
            try:
                file_control = FileControl.objects.get(id=file_ctrl_id)
                pet_file_ctrl = PetitionFileControl.objects.create(
                    petition=petition,
                    file_control=file_control)
            except FileControl.DoesNotExist:
                raise ParseError(
                    detail="No se envió un id de file_control válido")
            except Exception as e:
                raise ParseError(detail=e)
        for data_file in data_files:
            if is_dupl:
                data_file_id = data_file.id
                new_file = data_file
                new_file.pk = None
                new_file.petition_file_control = pet_file_ctrl
                new_file.save()
                new_file.change_status('initial')
            #if not is_dupl:
            else:
                data_file.petition_file_control = pet_file_ctrl
                data_file.save()
                #data_file.delete()
                #DataFile.objects.filter(id=data_file_id).delete()
    else:
        raise ParseError(detail="No se especificó correctamente el destino")

    petition_data = serializers.PetitionFullSerializer(petition).data
    data = {
        "petition": petition_data,
        "file_controls": EntityFileControlsSerializer(
            petition.entity).data["file_controls"],
    }
    return Response(data, status=status.HTTP_200_OK)


class DataFileViewSet(CreateRetrievView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    action_serializers = {
        "list": serializers.DataFileSerializer,
    }

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["put"], detail=True, url_path='move')
    def move(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        
        data_file = self.get_object()
        petition = data_file.petition_file_control.petition
        return move_and_duplicate([data_file], petition, request)

    @action(methods=["get"], detail=True, url_path='counting')
    def counting(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()

        data_file, errors, suffix = data_file.decompress_file()
        if not data_file:
            print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        #data_file.find_coincidences(file_ctrl, suffix, saved)

        data = data_file.count_file_rows()
        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True, url_path='explore')
    def explore(self, request, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        data_file = self.get_object()
        data = data_file.start_file_process(is_explore=True)
        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)

        def textNormalizer(text):
            import re
            import unidecode
            final_text = text.upper().strip()
            final_text = unidecode.unidecode(final_text)
            final_text = re.sub(r'[^A-Z][DE|DEL][^A-Z]', ' ', final_text)
            final_text = re.sub(r' +', ' ', final_text)
            final_text = re.sub(r'[^A-Z]', '', final_text)
            return final_text
        
        valid_fields = [
            "name_in_data", "column_type", "final_field", 
            "final_field__parameter_group", "data_type"]
        validated_data = data["structured_data"]
        current_sheets = data["current_sheets"]
        first_valid_sheet = None
        for sheet_name in current_sheets:
            sheet_data = validated_data[sheet_name]
            if "headers" in sheet_data and sheet_data["headers"]:
                first_valid_sheet = sheet_data
                break
        if not first_valid_sheet:
            first_valid_sheet = validated_data[current_sheets[0]]
            if not first_valid_sheet:
                return Response(
                    {"errors": ["WARNING: No se encontró algo que coincidiera"]},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                prov_headers = first_valid_sheet["all_data"][0]
                first_valid_sheet["complex_headers"] = [
                    {"position_in_data": posit}
                        for posit, head in enumerate(prov_headers, start=1)]
                return Response(
                    first_valid_sheet, status=status.HTTP_201_CREATED)
        print("DESPUÉS DE HEADER")
        try:
            headers = first_valid_sheet["headers"]
            complex_headers = []
            file_control = data_file.petition_file_control.file_control
            data_groups = [file_control.data_group.name, 'catalogs']
            print(data_groups)
            all_name_columns = NameColumn.objects\
                .filter(
                    final_field__isnull=False,
                    name_in_data__isnull=False,
                    final_field__parameter_group__data_group__name__in=data_groups,
                )\
                .values(*valid_fields)
            
            #.exclude(name_in_data__startswith="_")

            final_names = {}
            for name_col in all_name_columns:
                standard_name = textNormalizer(name_col["name_in_data"])
                unique_name = (
                    f'{standard_name}-{name_col["final_field"]}-'
                    f'{name_col["final_field__parameter_group"]}')
                if final_names.get(standard_name, False):
                    if not final_names[standard_name]["valid"]:
                        continue
                    elif final_names[standard_name]["unique_name"] != unique_name:
                        final_names[standard_name]["valid"] = False
                    continue
                else:
                    base_dict = {
                        "valid": True,
                        "unique_name": unique_name,
                        "standard_name": standard_name,
                    }
                    base_dict.update(name_col)
                    final_names[standard_name] = base_dict
            final_names = {
                name: vals for name, vals in final_names.items()
                    if vals["valid"]}
            for (position, header) in enumerate(headers, start=1):
                std_header = textNormalizer(header)
                base_dict = {"position_in_data": position}
                if final_names.get(std_header, False):
                    vals = final_names[std_header]
                    base_dict.update({field: vals[field] for field in valid_fields})
                base_dict["name_in_data"] = header
                complex_headers.append(base_dict)
            first_valid_sheet["complex_headers"] = complex_headers
        except Exception as e:
            print("HUBO UN ERRORZASO")
            print(e)
        #print(data["structured_data"][:6])
        return Response(
            first_valid_sheet, status=status.HTTP_201_CREATED)


class OpenDataInaiViewSet(ListRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataFile.objects.all()

    @action(methods=["post"], detail=False, url_path='insert_xls')
    def insert_xls(self, request, **kwargs):
        import json
        import zipfile
        import pandas as pd
        from datetime import datetime
        from scripts.import_inai import insert_from_json
        if not request.user.is_staff:
            raise PermissionDenied()

        zip_file = zipfile.ZipFile(request.FILES['file'])
        petitions = []
        for zip_elem in zip_file.infolist():
            file_bytes = zip_file.open(zip_elem).read()
            excel_file = pd.read_excel(
                file_bytes, sheet_name="Reporte", dtype='string',
                na_filter=False, keep_default_na=False)
            #print(excel_file)
            records = excel_file.to_dict(orient='records')
            petitions += records

        for pet in petitions:
            try:
                val = pet.get("Fecha de recepción", "01/01/2018") or "01/01/2018"
                pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')
            except Exception as e:
                print(pet)
                print(e)

        petitions = sorted(petitions, key=lambda i: i['fecha_orden'])


        """
        all_status = {}
        for petition in petitions:
            if petition["Estatus"] not in all_status:
                all_status[petition["Estatus"]] = [petition["Institución"]]
            else:
                all_status[petition["Estatus"]].append(petition["Institución"])
            #all_status[petition["Estatus"]] = True
        print("petitions", petitions)
        
        return Response(
            {"petitions": petitions}, status=status.HTTP_201_CREATED)
        """

        inai_fields = [
            {
                "inai_open_search": "Institución",
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "nombreSujetoObligado",
                "insert": True,
                "related": 'entity',
            },
            {
                "inai_open_search": "No. de folio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "folio_petition",
                "unique": True,
            },
            {
                "inai_open_search": False,
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "entity",
                "unique": True,
            },
            {
                "inai_open_search": "Descripción",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_petition",
                "transform": "add_br",
            },
            {
                "inai_open_search": "Fecha de recepción",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_petition",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "Estatus",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "status_petition",
                "related": "status_petition",
                "transform": "get_status_obj",
            },
            {
                "inai_open_search": "Respuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_response",
                "transform": "add_br",
            },
        ]

        spec_functions = [
            ("insert_between_months", False),
            ("add_limit_complain", True),
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search',
            special_functions=spec_functions)

        #if data.get("errors", False):
        #    return Response(
        #        data, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": True}, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path='insert_json')
    def insert_json(self, request, **kwargs):
        import json
        from datetime import datetime
        from scripts.import_inai import insert_from_json
        if not request.user.is_staff:
            raise PermissionDenied()
        data_json = request.data
        data = json.load(data_json["file"])

        petitions = data["solicitudes"]

        for pet in petitions:
            val = pet["fechaEnvio"]
            pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')

        petitions = sorted(petitions, key=lambda i: i['fecha_orden'])

        inai_fields = [
            {
                "inai_open_search": "idSujetoObligado",
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "idSujetoObligado",
                "related": 'entity',
            },
            {
                "inai_open_search": "nombreSujetoObligado",
                "model_name": "Entity",
                "app_name": "catalog",
                "final_field": "nombreSujetoObligado",
                # "insert": True,
                "related": 'entity',
            },
            {
                "inai_open_search": "dsFolio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "folio_petition",
                "unique": True,
            },
            {
                "inai_open_search": False,
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "entity",
                "unique": True,
            },
            {
                "inai_open_search": "descripcionSolicitud",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_petition",
                "transform": "unescape",
            },
            {
                "inai_open_search": "fechaEnvio",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_petition",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "descripcionRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "description_response",
                "transform": "unescape",
            },
            {
                "inai_open_search": "dtFechaUltimaRespuesta",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "send_response",
                "transform": "date_mex",
            },
            {
                "inai_open_search": "id",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "id_inai_open_data",
            },
            {
                "inai_open_search": "informacionQueja",
                "app_name": "inai",
                "model_name": "Petition",
                "final_field": "info_queja_inai",
                "transform": "to_json",
            },
        ]
        spec_functions = [
            ("join_url", True),
            ("join_lines", True),
            ("insert_between_months", False)
        ]
        insert_from_json(
            petitions, inai_fields, 'inai', 'Petition', 'inai_open_search', 
            special_functions=spec_functions)

        if data.get("errors", False):
            return Response(
                data, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            data, status=status.HTTP_201_CREATED)

