import io
from django.conf import settings

import csv
import uuid as uuid_lib

from inai.models import DataFile
delegation_value_list = [
    'name', 'other_names', 'state__short_name', 'id', 'clues']


def field_of_models(model_name):
    from django.apps import apps
    my_model = apps.get_model('formula', model_name)
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
        from inai.models import NameColumn
        self.data_file = data_file
        petition = data_file.petition_file_control.petition
        self.file_control = data_file.petition_file_control.file_control

        self.entity = petition.entity
        self.institution = self.entity.institution
        self.global_state = self.entity.state
        self.global_clues = self.entity.clues
        self.global_delegation = None
        if self.institution.code == "INSABI":
            if self.global_state:
                delegation_name = f"{self.global_state.short_name} - INSABI"
                self.global_delegation = Delegation.objects.filter(
                    name=delegation_name).first()
        elif self.global_clues:
            self.global_delegation = self.global_clues.related_delegation
        only_name = f"NEW_ELEM_NAME_{self.data_file.id}.csv"
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

        self.final_lists = [
            {"name": "prescription", "model": "Prescription"},
            {"name": "drug", "model": "Drug"},
            {"name": "missing_field", "model": "MissingField"},
            {"name": "missing_row", "model": "MissingRow"},
        ]
        self.model_fields = {curr_list["name"]: field_of_models(curr_list["model"])
                             for curr_list in self.final_lists}

        self.existing_fields = []
        self.catalog_clues_by_id = {}
        self.catalog_delegation = {}
        self.catalog_container = {}
        self.task_params = task_params

        # self.claves_medico_dict = {}
        # self.catalog_clues = {}
        # self.catalog_state = {}

    def build_csv_converted(self):
        from scripts.common import build_s3
        from task.serverless import start_build_csv_data, async_in_lambda
        # print("prescription_fields", prescription_fields, "\n\n")
        self.build_catalogs()
        self.build_catalog_container()

        self.build_existing_fields()
        has_minimals_criteria, detailed_criteria = \
            self.calculate_minimals_criteria()
        if not has_minimals_criteria:
            print("detailed_criteria", detailed_criteria)
            error = {"text": "No se encontraron todas las columnas esenciales",
                      "detailed_criteria": detailed_criteria}
            return [], [error], None

        string_date = self.get_date_format()
        # print("string_date", string_date)
        unique_clues = {}
        for existing_field in self.existing_fields:
            if existing_field["collection"] == "CLUES" and \
                    existing_field["is_unique"]:
                unique_clues = existing_field
                break

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
            "final_lists": self.final_lists,
            "model_fields": self.model_fields,
            "existing_fields": self.existing_fields,
            "catalog_delegation": self.catalog_delegation,
            "catalog_clues_by_id": self.catalog_clues_by_id,
            "catalog_container": self.catalog_container,
            "string_date": string_date,
            "unique_clues": unique_clues,
        }
        params = {
            "init_data": init_data,
            "s3": build_s3(),
            "file": self.data_file.file.name,
        }
        # result = start_build_csv_data(params, None)
        self.task_params["function_after"] = "finish_build_csv_data"
        self.task_params["models"] = [self.data_file]
        async_task = async_in_lambda(
            "start_build_csv_data", params, self.task_params)
        return async_task, [], None


    def save_result_csv(self, result_files):
        from category.models import FileType
        all_new_files = []
        for result_file in result_files:
            model_name = result_file["name"]
            file_type = FileType.objects.get(name=model_name)
            new_file = DataFile.objects.create(
                file=result_file["path"],
                origin_file=self.data_file,
                petition_file_control=self.data_file.petition_file_control,
                file_type=file_type,
            )
            new_file.change_status('initial')
            all_new_files.append(new_file)
            # self.send_csv_to_db(result_file["path"], model_name)
        return [], [], all_new_files

    def build_existing_fields(self):

        if self.existing_fields:
            return self.existing_fields

        simple_fields = [
            ["date_release"],
            ["date_visit"],
            ["date_delivery"],
            ["folio_document"],
            ["name:DocumentType", "document_type"],
            ["prescribed_amount"],
            ["delivered_amount"],
            ["budget_key"],
            ["key2:Container", "key2"],
            ["rn"],
            ["price:Drug", "price"],
            ["folio_document"],
            ["name:Delegation", "delegation_name"],
            ["clues:CLUES", "clave_clues"],
            ["key_issste:CLUES", "key_issste"],
            ["id_clues:CLUES", "id_clues"],
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
                    "collection": column.final_field.collection.model_name,
                    "is_unique": column.final_field.is_unique,
                    "data_type": column.final_field.data_type.name,
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
        some_medicine = has_matching_dict("name", "key2") or \
            has_matching_dict("name", "_own_key")
        if not some_medicine:
            for field in existing_fields:
                if field["name"] == "name" and field["collection"] == "Container":
                    some_medicine = True

        detailed_criteria = {
            "has_delegation": has_delegation,
            "some_data_time": some_data_time,
            "has_folio": has_folio,
            "some_amount": some_amount,
            "some_medicine": some_medicine,
        }
        every_criteria = True
        for value in detailed_criteria.values():
            if not value:
                every_criteria = False
                break
        return every_criteria, detailed_criteria

    def build_catalogs(self):

        columns = {"all": self.name_columns.values()}
        clues_unique = self.name_columns.filter(
            final_field__collection__model_name='CLUES',
            final_field__is_unique=True).first()
        if clues_unique:
            self.build_catalog_clues_by_id(clues_unique.final_field.name)
        columns["delegation"] = self.name_columns.filter(
            final_field__collection__model_name='Delegation').values()
        if not self.global_delegation and columns["delegation"]:
            self.build_catalog_delegation()

    def build_catalog_delegation(self):
        from catalog.models import Delegation

        curr_delegations = Delegation.objects.filter(institution=self.institution)
        if self.global_state:
            curr_delegations = curr_delegations.filter(state=self.global_state)
        delegations_query = list(curr_delegations.values(*delegation_value_list))
        for delegation in delegations_query:
            try:
                delegation_name = delegation["name"].upper()
            except Exception:
                delegation_name = delegation["name"].upper()
            if delegation_name not in self.catalog_delegation:
                self.catalog_delegation[delegation_name] = delegation
            alt_names = delegation["other_names"] or []
            for alt_name in alt_names:
                if alt_name not in self.catalog_delegation:
                    self.catalog_delegation[alt_name] = delegation
        # print("DELEGATIONS: \n", self.catalog_delegation)

    def build_catalog_clues_by_id(self, key_field):
        from catalog.models import CLUES
        clues_data_query = CLUES.objects.filter(institution=self.institution)
        if self.global_state:
            clues_data_query.filter(state=self.global_state)
        value_list = ["id", key_field]
        clues_data_list = list(clues_data_query.values(*value_list))
        for clues_data in clues_data_list:
            clues_key = clues_data[key_field]
            self.catalog_clues_by_id[clues_key] = clues_data["id"]

    def build_catalog_container(self):
        from medicine.models import Container
        all_containers = Container.objects.all()
        containers_query = list(all_containers.values('key2', 'id'))
        for container in containers_query:
            self.catalog_container[container["key2"]] = container["id"]

    def get_date_format(self):
        from inai.models import Transformation
        transformation = Transformation.objects.filter(
            clean_function__name="format_date",
            file_control=self.file_control).first()
        return transformation.addl_params["value"] \
            if transformation else '%Y-%m-%d %H:%M:%S.%f'

    # ########## FUNCIONES AUXILIARES #############
    def send_csv_to_db(self, path, model_name):
        import psycopg2
        columns = self.model_fields[model_name]
        columns_join = ",".join(columns)
        model_in_db = f"formula_{model_name.lower()}"
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        region_name = getattr(settings, "AWS_S3_REGION_NAME")
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        aws_location = getattr(settings, "AWS_LOCATION")
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
        connection = psycopg2.connect(
            database=desabasto_db.get("NAME"),
            user=desabasto_db.get("USER"),
            password=desabasto_db.get("PASSWORD"),
            host=desabasto_db.get("HOST"),
            port=desabasto_db.get("PORT"))
        cursor = connection.cursor()
        cursor.execute(sql_query)
        connection.commit()
        cursor.close()
        connection.close()

    def create_delegation(self, delegation_name, clues_id):
        from catalog.models import Delegation, CLUES
        if self.institution.code in ["ISSSTE", "IMSS"]:
            try:
                clues_obj = CLUES.objects.get(id=clues_id)
                del_obj, created = Delegation.objects.get_or_create(
                    institution=self.institution,
                    name=delegation_name,
                    clues=clues_obj,
                    state=clues_obj.state,
                )
                delegation_id = del_obj.id
                final_delegation = {}
                for field in delegation_value_list:
                    final_delegation[field] = getattr(del_obj, field)
                self.catalog_delegation[delegation_name] = final_delegation
                return delegation_id, None
            except Exception as e:
                return None, "No se pudo crear la delegación, ERROR: %s" % e
        else:
            error = "Por alguna razón, no es ISSSTE o IMSS y no tiene delegación"
            return None, error

