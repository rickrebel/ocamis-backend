import io
from django.conf import settings
from scripts.common import start_session, create_file
import csv
import uuid as uuid_lib

from inai.models import DataFile
delegation_value_list = [
    'name', 'other_names', 'state__short_name', 'id', 'clues']


def text_normalizer(text):
    import re
    import unidecode
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)


def field_of_models(model_data):
    from django.apps import apps
    app_name = model_data.get('app', 'formula')
    model_name = model_data['model']
    my_model = apps.get_model(app_name, model_name)
    all_fields = my_model._meta.get_fields(
        include_parents=False, include_hidden=False)
    field_names = []
    for field in all_fields:
        if field.one_to_many:
            continue
        complement = "_id" if field.is_relation else ""
        field_names.append(f"{field.name}{complement}")
    return field_names


class Match:

    def __init__(self, data_file: DataFile, task_params=None):
        from inai.models import set_upload_path
        from catalog.models import Delegation
        from data_param.models import NameColumn
        self.data_file = data_file
        self.lap = self.data_file.next_lap
        petition = data_file.petition_file_control.petition
        self.file_control = data_file.petition_file_control.file_control
        self.entity = petition.entity
        self.institution = self.entity.institution
        self.global_state = self.entity.state
        self.global_clues = self.entity.clues
        self.global_delegation = None
        print("self.institution.code", self.institution.code)
        if self.institution.code == "INSABI":
            print("INSABI")
            if self.global_state:
                delegation_name = f"{self.global_state.short_name} - INSABI"
                self.global_delegation = Delegation.objects.filter(
                    name=delegation_name).first()
        elif self.global_clues:
            self.global_delegation = self.global_clues.related_delegation
        print("global_delegation", self.global_delegation)
        only_name = f"NEW_ELEM_NAME_{self.data_file.id}_lap{self.lap}.csv"
        self.final_path = set_upload_path(self.data_file, only_name)
        self.name_columns = NameColumn.objects \
            .filter(file_control=self.file_control) \
            .prefetch_related(
                "final_field",
                "final_field__collection",
                "final_field__parameter_group",
            )

        original_columns = self.name_columns.filter(
            position_in_data__isnull=False)
        self.delimiter = self.file_control.delimiter or ','
        self.columns_count = original_columns.count()

        self.editable_models = [
            {"name": "prescription", "model": "Prescription"},
            {"name": "drug", "model": "Drug"},
            {"name": "missing_field", "model": "MissingField"},
            {"name": "missing_row", "model": "MissingRow"},

            {"name": "doctor", "model": "Doctor"},
            {"name": "diagnosis", "model": "Diagnosis"},
            {"name": "area", "model": "Area", "app": "catalog"},
        ]
        self.model_fields = {curr_list["name"]: field_of_models(curr_list)
                             for curr_list in self.editable_models}

        self.existing_fields = []
        self.catalogs = {}
        # self.catalog_clues_by_id = None
        # self.catalog_delegation_by_id = {}
        # self.catalog_container = {}
        self.task_params = task_params

        s3_client, dev_resource = start_session()
        self.s3_client = s3_client

        # self.claves_medico_dict = {}
        # self.catalog_clues = {}
        # self.catalog_state = {}

    def build_csv_converted(self, is_prepare=False):
        from scripts.common import build_s3
        from task.serverless import async_in_lambda

        string_date = self.get_date_format()
        missing_criteria = self.calculate_minimals_criteria()
        if not string_date:
            missing_criteria.append("Sin formato de fecha")
        if missing_criteria:
            print("missing_criteria", missing_criteria)
            error = f"No se encontraron todas las columnas esenciales; " \
                f"Elementos faltantes: {missing_criteria}"
            return [], [error], self.data_file


        self.build_all_catalogs()
        self.build_existing_fields()

        # print("string_date", string_date)
        # unique_clues = {}
        # for existing_field in self.existing_fields:
        #     if existing_field["collection"] == "CLUES" and \
        #             existing_field["is_unique"]:
        #         unique_clues = existing_field
        #         break


        init_data = {
            "data_file_id": self.data_file.id,
            # "file_control_id": self.file_control.id,
            "global_delegation_id": self.global_delegation.id if self.global_delegation else None,
            "decode": self.file_control.decode,
            "delimiter": self.delimiter,
            "final_path": self.final_path,
            "row_start_data": self.file_control.row_start_data,
            "entity_id": self.entity.id if self.entity else None,
            "institution_id": self.institution.id if self.institution else None,
            "global_clues_id": self.global_clues.id if self.global_clues else None,
            "columns_count": self.columns_count,
            "editable_models": self.editable_models,
            "model_fields": self.model_fields,
            "existing_fields": self.existing_fields,
            "catalogs": self.catalogs,
            "is_prepare": is_prepare,
            "lap": -1 if is_prepare else self.lap,
            # "catalog_delegation": self.catalog_delegation_by_id,
            # "catalog_clues_by_id": self.catalog_clues_by_id,
            # "catalog_container": self.catalog_container,
            "string_date": string_date,
            # "unique_clues": unique_clues,
        }
        # result = start_build_csv_data(params, None)
        self.task_params["function_after"] = "finish_build_csv_data"
        all_tasks = []
        print("is_prepare", is_prepare)
        for sheet_file in self.data_file.sheet_files.filter(matched=True):

            if sheet_file.sheet_name not in self.data_file.filtered_sheets:
                continue
            self.task_params["models"] = [sheet_file]
            if is_prepare:
                init_data["sample_data"] = sheet_file.sample_data
            params = {
                "init_data": init_data,
                "s3": build_s3(),
                "file": sheet_file.file.name,
            }
            async_task = async_in_lambda(
                "start_build_csv_data", params, self.task_params)
            all_tasks.append(async_task)
        return all_tasks, [], self.data_file

    def build_existing_fields(self):

        if self.existing_fields:
            return self.existing_fields

        simple_fields = [
            # Generales receta
            ["date_release"],
            ["date_visit"],
            ["date_delivery"],
            ["folio_document"],
            ["name:DocumentType", "document_type"],
            ["prescribed_amount"],
            ["delivered_amount"],
            # Medicamento
            ["key2:Container", "key2"],
            ["price:Drug", "price"],
            # Diagnósticos
            ["motive"],
            ["cie10"],
            ["text:Diagnosis", "diagnosis"],
            # Geográficos
            ["name:Delegation", "delegation_name"],
            ["clues:CLUES", "clave_clues"],
            ["key_issste:CLUES", "key_issste"],
            ["id_clues:CLUES", "id_clues"],
            # Doctores
            ["professional_license"],
            ["medical_speciality"],
            ["clave:Doctor", "clave"],
            ["full_name"],
            # Areas
            ["description:Area", "area_description"],
            ["name:Area", "area_name"],
            ["key:Area", "area_key"],
        ]

        for simple_field in simple_fields:
            field_name = simple_field[0].split(":")
            name_to_local = simple_field[1] \
                if len(simple_field) > 1 else field_name[0]
            query_fields = {"final_field__name": field_name[0]}
            if len(field_name) > 1:
                query_fields["final_field__collection__model_name"] = field_name[1]
            column = self.name_columns.filter(**query_fields).first()
            if column:
                self.existing_fields.append({
                    "name": name_to_local,
                    "name_column": column.id,
                    "position": column.position_in_data,
                    "final_field_id": column.final_field.id,
                    "collection": column.final_field.collection.model_name,
                    "is_unique": column.final_field.is_unique,
                    "data_type": column.final_field.data_type.name,
                    "regex_format": column.final_field.regex_format,
                })
        if not self.existing_fields:
            raise Exception("No se encontraron campos para crear las recetas")
        return self.existing_fields

    def calculate_minimals_criteria(self):

        existing_fields = self.build_existing_fields()

        def has_matching_dict(key, value):
            for dict_item in existing_fields:
                if dict_item[key] == value:
                    return True
            return False

        has_delegation = bool(self.global_delegation)
        if not has_delegation:
            has_delegation = has_matching_dict("collection", "Delegation")
        some_data_time = has_matching_dict("data_type", "Datetime")
        has_folio = has_matching_dict("name", "folio_document")
        some_amount = self.name_columns\
            .filter(final_field__name__contains="amount").exists()
        key_medicine = has_matching_dict("name", "key2")
        some_medicine = has_matching_dict("name", "_own_key")
        if not some_medicine:
            for field in existing_fields:
                if field["name"] == "name" and field["collection"] == "Container":
                    some_medicine = True

        detailed_criteria = {
            "Datos de delegación": has_delegation,
            "Alguna fecha": some_data_time,
            "Folio de receta": has_folio,
            "Alguna cantidad": some_amount,
            "Clave de medicamento": key_medicine,
            # "Identificador de medicamento": some_medicine,
        }
        missing_criteria = []
        for criteria_name, value in detailed_criteria.items():
            if not value:
                missing_criteria.append(criteria_name)
        if not key_medicine:
            if some_medicine:
                missing_criteria.append(
                    "Hay medicamentos, pero aún no los procesamos")
            else:
                missing_criteria.append("Algún medicamentos")
        return missing_criteria

    def build_all_catalogs(self):
        catalogs = {
            "container": {
                "model2": "medicine:Container",
                "only_unique": True,
                "required": False,
                "value_list": [
                    "name", "presentation__description",
                    "presentation__presentation_type__name",
                    "presentation__component__name"]
            },
            "diagnosis": {
                "model2": "formula:Diagnosis",
                "only_unique": False,
                "required": False,
                "id": "uuid",
                "value_list": ["motive", "cie10", "text"],
            },
            "area": {
                "model2": "catalog:Area",
                "only_unique": False,
                "required": False,
                "by_entity": True,
                "id": "uuid",
                "value_list": ["description", "name", "key"],
            },
            "doctor": {
                "model2": "formula:Doctor",
                "only_unique": False,
                "required": False,
                "by_entity": True,
                "id": "uuid",
                "value_list": [
                    "full_name", "professional_license",
                    "clave", "medical_speciality"],
            },
        }
        if not self.global_clues:
            catalogs["clues"] = {
                "model2": "catalog:CLUES",
                "only_unique": True,
                "required": True,
                "by_entity": True,
                "value_list": [
                    'name', 'state__short_name', 'typology', 'typology_cve',
                    'jurisdiction', 'atention_level'],
            }
        if not self.global_delegation:
            catalogs["delegation"] = {
                "model2": "catalog:Delegation",
                "only_unique": True,
                "required": True,
                "by_entity": True,
                "complement_field": "other_names",
                "value_list": ['name', 'state__short_name', 'clues'],
            }
        for [catalog_name, catalog] in catalogs.items():
            # if catalog.get("by_entity", False):
            #     catalog["entity"] = self.entity
            dict_file = self.build_catalog(catalog_name, **catalog)
            # file_name = dict_file.file.name if dict_file else None
            # file_name = self.build_catalog(catalog_name, **catalog)
            if dict_file:
                self.catalogs[catalog_name] = {
                    "name": catalog_name,
                    "file": dict_file.file.name,
                    "unique_field": dict_file.unique_field.name,
                    "unique_field_id": dict_file.unique_field.id,
                    "collection": dict_file.collection.model_name,
                    "params": catalog,
                }
            elif catalog["required"]:
                print("dict_file", dict_file)
                raise Exception(f"Error al crear el catálogo de {catalog_name}")

    def build_catalog(self, catalog_name, model2, only_unique, **kwargs):
        from data_param.models import DictionaryFile
        from django.apps import apps
        [app_name, model_name] = model2.split(":", 1)
        model = apps.get_model(app_name, model_name)
        query_unique = {"final_field__collection__model_name": model_name}
        if only_unique:
            query_unique["final_field__is_unique"] = True
        model_unique = self.name_columns.filter(**query_unique)\
            .order_by('-final_field__is_unique').first()
        if not model_unique:
            return None
        query_dict_file = {"collection": model_unique.final_field.collection,
                           "unique_field": model_unique.final_field}
        # entity = kwargs.get("entity")
        if kwargs.get("by_entity"):
            # query_dict_file["entity"] = self.entity
            query_dict_file["institution"] = self.institution
            if self.global_delegation:
                query_dict_file["delegation"] = self.global_delegation
        dict_file = DictionaryFile.objects.filter(**query_dict_file).first()
        if not dict_file:
            query_dict_file["file"] = self.build_catalog_by_id(
                model, model_unique.final_field.name, catalog_name, **kwargs)
            dict_file = DictionaryFile.objects.create(**query_dict_file)
        return dict_file

    def build_catalog_by_id(
            self, model, key_field, catalog_name, **kwargs):
        import json
        query_filter = {f"{key_field}__isnull": False}
        if kwargs.get("by_entity"):
            query_filter["institution"] = self.institution
            if catalog_name == "clues":
                if self.global_clues:
                    query_filter["clues"] = self.global_clues
                if self.global_state:
                    query_filter["state"] = self.global_state
            elif self.global_delegation:
                query_filter["delegation"] = self.global_delegation
        model_query = model.objects.filter(**query_filter)
        complement_field = kwargs.get("complement_field")
        value_list = kwargs.get("value_list")
        field_id = kwargs.get("id", "id")
        list_values = value_list + [key_field, field_id]
        if complement_field:
            list_values.append(complement_field)
        model_list = list(model_query.values(*list_values))
        catalog_model = {}
        for elem in model_list:
            catalog_model[elem[key_field]] = elem
            if complement_field:
                complement_list = elem[complement_field] or []
                for name in complement_list:
                    if name not in catalog_model:
                        catalog_model[name] = elem
        final_path = f"catalogs/{model.__name__.lower()}_by_{key_field}.json"
        if kwargs.get("by_entity"):
            final_path = f"{self.entity.acronym}/{final_path}"
        dumb_catalog = json.dumps(catalog_model)
        file_model, errors = create_file(
            dumb_catalog, self.s3_client, final_path=final_path)
        if errors:
            raise Exception(f"Error creando catálogo {catalog_name}: {errors}")
        return file_model

    def get_date_format(self):
        from data_param.models import Transformation
        transformation = Transformation.objects.filter(
            clean_function__name="format_date",
            file_control=self.file_control).first()
        if not transformation:
            transformation = Transformation.objects.filter(
                clean_function__name="format_date",
                name_column__file_control=self.file_control).first()
        return transformation.addl_params.get("value") \
            if transformation else None  # '%Y-%m-%d %H:%M:%S.%fYYY'

    # ########## FUNCIONES AUXILIARES #############
    def send_csv_to_db(self, path, model_name):
        from task.serverless import async_in_lambda

        model_in_db = f"formula_{model_name.lower()}"
        columns = self.model_fields[model_name]
        columns_join = ",".join(columns)
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_location = getattr(settings, "AWS_LOCATION")
        region_name = getattr(settings, "AWS_S3_REGION_NAME")
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        sql_query = f"""
            SELECT aws_s3.table_import_from_s3(
                '{model_in_db}',
                '{columns_join}',
                '(format csv, header false, delimiter "|", encoding "LATIN1")',
                '{bucket_name}',
                '{aws_location}/{path}',
                '{region_name}',
                '{access_key}',
                '{secret_key}'
            )
        """
        desabasto_db = getattr(settings, "DATABASES", {}).get("default")
        # save_csv_in_db(sql_query, desabasto_db)
        params = {
            "sql_query": sql_query,
            "db_config": desabasto_db,
        }
        self.task_params["models"] = [self.data_file]
        self.task_params["function_after"] = "check_success_insert"
        return async_in_lambda("save_csv_in_db", params, self.task_params)

    # def build_catalog_clues(self):
    #     from data_param.models import DictionaryFile
    #     clues_unique = self.name_columns.filter(
    #         final_field__collection__model_name='CLUES',
    #         final_field__is_unique=True).first()
    #     if not clues_unique:
    #         raise Exception("No se encontró un campo único para CLUES")
    #     dict_file = DictionaryFile.objects.filter(
    #         collection__model_name='CLUES',
    #         entity=self.entity,
    #         unique_field=clues_unique.final_field).first()
    #     if not dict_file:
    #         file_clues, errors = self.build_catalog_clues_by_id(
    #             clues_unique.final_field.name)
    #         if errors:
    #             raise Exception(f"Error al crear el catálogo de CLUES:"
    #                             f" {errors}")
    #         dict_file = DictionaryFile.objects.create(
    #             collection=clues_unique.final_field.collection,
    #             entity=self.entity,
    #             unique_field=clues_unique.final_field,
    #             file=file_clues,
    #         )
    #     return dict_file.file.name
    #
    # def build_catalog_delegation(self):
    #     from data_param.models import DictionaryFile
    #     has_delegation_fields = self.name_columns.filter(
    #         final_field__collection__model_name='Delegation').exists()
    #     if not has_delegation_fields:
    #         raise Exception("No se encontró un campo para construir delegación")
    #     delegation_unique = self.name_columns.filter(
    #         final_field__collection__model_name='Delegation',
    #         final_field__is_unique=True).first()
    #     if not delegation_unique:
    #         raise Exception("No se encontró un campo único para Delegación")
    #     dict_file = DictionaryFile.objects.filter(
    #         collection__model_name='Delegation',
    #         entity=self.entity,
    #         unique_field=delegation_unique.final_field).first()
    #     if not dict_file:
    #         file_delegation, errors = self.build_catalog_delegation_by_id(
    #             delegation_unique.final_field.name)
    #         if errors:
    #             raise Exception(f"Error al crear el catálogo de Delegación:"
    #                             f" {errors}")
    #         dict_file = DictionaryFile.objects.create(
    #             collection=delegation_unique.final_field.collection,
    #             entity=self.entity,
    #             unique_field=delegation_unique.final_field,
    #             file=file_delegation,
    #         )
    #     return dict_file.file.name
    #
    # def build_catalog_delegation_by_id(self, key_field='name'):
    #     from catalog.models import Delegation
    #     curr_delegations = Delegation.objects.filter(institution=self.institution)
    #     if self.global_state:
    #         curr_delegations = curr_delegations.filter(state=self.global_state)
    #     delegations_query = list(curr_delegations.values(*delegation_value_list))
    #     catalog_delegation = {}
    #     for delegation in delegations_query:
    #         delegation_name = text_normalizer(delegation[key_field])
    #         if delegation_name not in catalog_delegation:
    #             catalog_delegation[delegation_name] = delegation
    #         alt_names = delegation["other_names"] or []
    #         for alt_name in alt_names:
    #             alt_name = text_normalizer(alt_name)
    #             if alt_name not in catalog_delegation:
    #                 catalog_delegation[alt_name] = delegation
    #     final_path = f"{self.entity.acronym}/catalogs/delegation_by_{key_field}.json"
    #     file_name, errors = create_file(
    #         catalog_delegation, self.s3_client, final_path=final_path)
    #     return file_name, errors
    #
    # def build_catalog_clues_by_id(self, key_field):
    #     from catalog.models import CLUES
    #     clues_data_query = CLUES.objects.filter(institution=self.institution)
    #     if self.global_state:
    #         clues_data_query.filter(state=self.global_state)
    #     value_list = ["id", key_field]
    #     clues_data_list = list(clues_data_query.values(*value_list))
    #     catalog_clues = {}
    #     for clues_data in clues_data_list:
    #         clues_key = clues_data[key_field]
    #         catalog_clues[clues_key] = clues_data["id"]
    #     final_path = f"{self.entity.acronym}/catalogs/clues_by_{key_field}.json"
    #     file_name, errors = create_file(
    #         catalog_clues, self.s3_client, final_path=final_path)
    #     return file_name, errors
    #
    # def build_catalog_container(self):
    #     from data_param.models import DictionaryFile
    #     container_unique = self.name_columns.filter(
    #         final_field__collection__model_name='Container',
    #         final_field__is_unique=True).first()
    #     if not container_unique:
    #         return None
    #     dict_file = DictionaryFile.objects.filter(
    #         collection__model_name='Container',
    #         unique_field=container_unique.final_field).first()
    #     if not dict_file:
    #         file_container, errors = self.build_catalog_container_by_id(
    #             container_unique.final_field.name)
    #         if errors:
    #             raise Exception(f"Error al crear el catálogo de Medicamentos aceptable:"
    #                             f" {errors}")
    #         dict_file = DictionaryFile.objects.create(
    #             collection=container_unique.final_field.collection,
    #             unique_field=container_unique.final_field,
    #             file=file_container,
    #         )
    #     return dict_file.file.name
    #
    # def build_catalog_container_by_id(self, key_field):
    #     from medicine.models import Container
    #     query_filter = {f"{key_field}__isnull": False}
    #     containers_query = Container.objects.filter(**query_filter)
    #     containers_list = list(containers_query.values("id", key_field))
    #     catalog_container = {}
    #     for container in containers_list:
    #         catalog_container[container[key_field]] = container["id"]
    #     final_path = f"catalogs/container_by_{key_field}.json"
    #     # return file_name, errors
    #     return create_file(
    #         catalog_container, self.s3_client, final_path=final_path)
    #
    # def build_catalog_diagnosis(self):
    #     from data_param.models import DictionaryFile
    #     diagnosis_unique = self.name_columns.filter(
    #         final_field__collection__model_name='Diagnosis',
    #         final_field__is_unique=True).first()
    #     if not diagnosis_unique:
    #         diagnosis_unique = self.name_columns.filter(
    #             final_field__collection__model_name='Diagnosis').first()
    #     if not diagnosis_unique:
    #         return False
    #     dict_file = DictionaryFile.objects.filter(
    #         collection__model_name='Diagnosis',
    #         unique_field=diagnosis_unique.final_field).first()
    #     if not dict_file:
    #         file_diagnosis, errors = self.build_catalog_diagnosis_by_id(
    #             diagnosis_unique.final_field.name)
    #         if errors:
    #             raise Exception(f"Error al crear el catálogo de Diagnóstico:"
    #                             f" {errors}")
    #         dict_file = DictionaryFile.objects.create(
    #             collection=diagnosis_unique.final_field.collection,
    #             unique_field=diagnosis_unique.final_field,
    #             file=file_diagnosis,
    #         )
    #     return dict_file.file.name
    #
    # def build_catalog_diagnosis_by_id(self, key_field):
    #     from formula.models import Diagnosis
    #     query_filter = {f"{key_field}__isnull": False}
    #     diagnosis_query = Diagnosis.objects.filter(**query_filter)
    #     diagnosis_list = list(diagnosis_query.values("id", key_field))
    #     catalog_diagnosis = {diagnosis[key_field]: diagnosis["id"]
    #                          for diagnosis in diagnosis_list}
    #     final_path = f"catalogs/diagnosis_by_{key_field}.json"
    #     return create_file(
    #         catalog_diagnosis, self.s3_client, final_path=final_path)
    #
    # def build_catalog_area(self):
    #     from data_param.models import DictionaryFile
    #     area_unique = self.name_columns.filter(
    #         final_field__collection__model_name='Area')\
    #         .order_by('-final_field__is_unique').first()
    #     if not area_unique:
    #         return None
    #     dict_file = DictionaryFile.objects.filter(
    #         collection__model_name='Area',
    #         entity=self.entity,
    #         unique_field=area_unique.final_field).first()
    #     if not dict_file:
    #         file_area, errors = self.build_catalog_area_by_id(
    #             area_unique.final_field.name)
    #         if errors:
    #             raise Exception(f"Error al crear el catálogo de Áreas:"
    #                             f" {errors}")
    #         dict_file = DictionaryFile.objects.create(
    #             collection=area_unique.final_field.collection,
    #             unique_field=area_unique.final_field,
    #             entity=self.entity,
    #             file=file_area,
    #         )
    #     return dict_file.file.name
    #
    # def build_catalog_area_by_id(self, key_field):
    #     from catalog.models import Area
    #     query_filter = {f"{key_field}__isnull": False, "entity": self.entity}
    #     areas_query = Area.objects.filter(**query_filter)
    #     areas_list = list(areas_query.values("id", key_field))
    #     catalog_area = {area[key_field]: area["id"]
    #                     for area in areas_list}
    #     final_path = f"{self.entity.acronym}/catalogs/area_by_{key_field}.json"
    #     return create_file(
    #         catalog_area, self.s3_client, final_path=final_path)
