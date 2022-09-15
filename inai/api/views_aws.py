# -*- coding: utf-8 -*-
from . import serializers
from rest_framework.response import Response
from rest_framework import (permissions, views, status)
from rest_framework.decorators import action
import unidecode

from inai.models import DataFile, NameColumn, Petition

from api.mixins import (
    ListMix, MultiSerializerListRetrieveUpdateMix as ListRetrieveUpdateMix,
    MultiSerializerCreateRetrieveMix as CreateRetrievView,
    MultiSerializerListRetrieveMix as ListRetrieveView)

from rest_framework.exceptions import (PermissionDenied, ValidationError)



class AutoExplorePetitionViewSet(ListRetrieveView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.PetitionEditSerializer
    queryset = Petition.objects.all()
    action_serializers = {
        "retrieve": serializers.PetitionFullSerializer,
    }

    def retrieve(self, request, pk=None):
        #self.check_permissions(request)
        from io import BytesIO
        import zipfile
        import rarfile
        import pathlib
        import boto3
        from inai.models import set_upload_path
        from django.conf import settings
        from django.core.files import File
        from inai.models import (
            ProcessFile, FileControl, PetitionFileControl)
        from category.models import FileType, StatusControl
        from data_param.models import DataGroup

        is_prod = getattr(settings, "IS_PRODUCTION", False)
        all_errors = []

        if is_prod:
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
            aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
            aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
            #s3 = boto3.resource(
            s3 = boto3.client(
                's3', aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key)
            dev_resource = boto3.resource(
                's3', aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key)

        petition = self.get_object()
        current_file_ctrl = request.query_params.get("file_ctrl", False)

        process_files = ProcessFile.objects.filter(
            petition=petition, has_data=True)
        data_group = DataGroup.objects.get(name="orphan")
        file_type = FileType.objects.get(name="with_data")
        name_control = "Archivos por agrupar. Petición %s" % (
            petition.folio_petition)
        initial_status = StatusControl.objects.get(
            name='initial', group="process")
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
            path = process_file.file.name
            suffixes = pathlib.Path(process_file.final_path).suffixes
            suffixes = set([suffix.lower() for suffix in suffixes])

            if is_prod:
                zip_obj = dev_resource.Object(
                    bucket_name=bucket_name, 
                    key=f"{settings.AWS_LOCATION}/{process_file.file.name}"
                    )
                buffer = BytesIO(zip_obj.get()["Body"].read()) 
            else:
                buffer = process_file.final_path

            if '.zip' in suffixes:
                zip_file = zipfile.ZipFile(buffer) 
            elif '.rar' in suffixes:
                zip_file = rarfile.RarFile(buffer)
            else:
                continue

            #s3 = boto3.resource(
            #    's3', aws_access_key_id=aws_access_key_id,
            #    aws_secret_access_key=aws_secret_access_key)
            #content_object = s3.Object(
            #    bucket_name, "data_files/%s" % self.file.name)

            for zip_elem in zip_file.infolist():
                if zip_elem.is_dir():
                    continue
                pos_slash = zip_elem.filename.rfind("/")
                only_name = zip_elem.filename[pos_slash + 1:]
                directory = (zip_elem.filename[:pos_slash]
                    if pos_slash > 0 else None)
                #z_file.open(filename).read()
                file_bytes = zip_file.open(zip_elem).read()

                try:
                    if is_prod:
                        final_path = set_upload_path(process_file, only_name)
                        success_file = s3.put_object(
                            Key=f"{settings.AWS_LOCATION}/{final_path}",
                            Body=file_bytes,
                            Bucket=bucket_name,
                            ACL='public-read',
                            #ContentType='application/pdf'
                        )
                        if success_file:
                            curr_file= f"{settings.AWS_LOCATION}{final_path}"
                        else:
                            all_errors += [f"No se pudo insertar el archivo {final_path}"]
                            continue
                    else:
                        curr_file = File(BytesIO(file_bytes), name=only_name)
                except Exception as e:
                    print(e)
                    all_errors += [u"Error leyendo los datos %s" % e]
                    continue
                new_file = DataFile.objects.create(
                    file=curr_file,
                    process_file=process_file,
                    directory=directory,
                    status_process=initial_status,
                    petition_file_control=pet_file_ctrl,
                    )


        all_data_files = DataFile.objects.filter(
            petition_file_control=pet_file_ctrl).order_by("date")

        last_file_control = None
        entity_file_controls = FileControl.objects.filter(
            petition_file_control__petition__entity=petition.entity)\
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
        success_explore = StatusControl.objects.get(
            name='success_exploration', group="process")
        explore_fail = StatusControl.objects.get(
            name='explore_fail', group="process")

        all_file_controls = near_file_controls | others_file_controls
        for data_file in all_data_files:
            saved = False
            data_file.error_process = []
            data_file.save()
            errors, suffix = data_file.decompress_file()
            for file_ctrl in all_file_controls:
                data = data_file.transform_file_in_data(
                    True, suffix, file_ctrl)
                if not data:
                    continue
                if isinstance(data, dict):
                    if data.get("errors", False):
                        #print(data)
                        continue
                #row_headers = file_ctrl.row_headers or 0
                headers = data["headers"]
                headers = [head.strip() for head in headers]
                #headers = validated_rows[row_headers-1] if row_headers else []
                #validated_rows = validated_rows[file_ctrl.row_start_data-1:]
                name_columns = NameColumn.objects.filter(
                        file_control=file_ctrl, name_in_data__isnull=False)\
                    .values_list("name_in_data", flat=True)
                if list(name_columns) == headers:
                    succ_pet_file_ctrl, created_pfc = PetitionFileControl.objects\
                        .get_or_create(
                            file_control=file_ctrl, petition=petition)
                    data_file.petition_file_control = succ_pet_file_ctrl
                    data_file.status_process = success_explore
                    data_file.save()
                    saved = True
                    break
            if not saved:
                data_file.status_process = explore_fail
                data_file.save()
        queryset = FileControl.objects\
            .filter(petition_file_control__petition__entity=petition.entity)\
            .distinct()\
            .prefetch_related(
                "data_group",
                "file_type",
                "columns",
                "columns__column_transformations",
                "petition_file_control",
                "petition_file_control__data_files",
                "petition_file_control__data_files__origin_file",
            )

        petition_data = serializers.PetitionFullSerializer(petition).data
        data = {
            "errors": all_errors,
            "petition": petition_data,
            "file_controls": serializers.FileControlFullSerializer(
                queryset, many=True).data,
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
        try:
            headers = data["headers"]
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
                standar_name = textNormalizer(name_col["name_in_data"])
                unique_name = (
                    f'{standar_name}-{name_col["final_field"]}-'
                    f'{name_col["final_field__parameter_group"]}')
                if final_names.get(standar_name, False):
                    if not final_names[standar_name]["valid"]:
                        continue
                    elif final_names[standar_name]["unique_name"] != unique_name:
                        final_names[standar_name]["valid"] = False
                    continue
                else:
                    base_dict = {
                        "valid": True,
                        "unique_name": unique_name,
                        "standar_name": standar_name
                    }
                    base_dict.update(name_col)
                    final_names[standar_name] = base_dict
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
            data["complex_headers"] = complex_headers
        except Exception as e:
            print("HUBO UN ERRORZASO")
            print(e)
        #print(data["structured_data"][:6])
        return Response(
            data, status=status.HTTP_201_CREATED)


class OpenDataInaiViewSet(ListRetrieveView):
    queryset = DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataFile.objects.all()

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
                "insert": True,
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

