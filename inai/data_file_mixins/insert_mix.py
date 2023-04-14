from django.conf import settings
from django.apps import apps
from django.db import connection
from django.db.models import Index
from inai.models import DataFile, TableFile


def create_constraints_and_indexes(model_name, app_label):
    model = apps.get_model(app_label, model_name)
    schema_editor = connection.schema_editor()
    with schema_editor.connection.cursor() as cursor:
        schema_editor.deferred_sql = []  # Clear any deferred SQL from previous operations
        real_model_name = f"{app_label}_{model_name.lower()}"
        for field in model._meta.get_fields():
            if field.remote_field and field.db_constraint:
                schema_editor.execute(schema_editor._create_fk_sql(
                    model, field, '_fk_%(to_table)s_%(to_column)s'))
                index_name = schema_editor._create_index_name(
                    real_model_name, [field.column])
                temp_index = Index(
                    fields=[field.name],
                    name=index_name)
                schema_editor.execute(schema_editor._create_index_sql(
                    model, fields=[field], name=temp_index.name))
        primary_key_field = model._meta.pk
        primary_key_name = f"{real_model_name}_pkey"
        schema_editor.execute(
            schema_editor.sql_create_pk % {
                "table": schema_editor.quote_name(model._meta.db_table),
                "name": schema_editor.quote_name(primary_key_name),
                "columns": schema_editor.quote_name(primary_key_field.column),
            }
        )
        alter_statements = schema_editor.deferred_sql

    return alter_statements


def delete_constraints_and_indexes(model_name, app_label):
    model = apps.get_model(app_label, model_name)
    schema_editor = connection.schema_editor()
    with schema_editor.connection.cursor() as cursor:
        real_model_name = f"{app_label}_{model_name.lower()}"
        schema_editor.deferred_sql = []  # Clear any deferred SQL from previous operations
        all_constraints = schema_editor._constraint_names(model)
        for constraint_name in all_constraints:
            try:
                schema_editor.execute(schema_editor._delete_check_sql(
                    model, constraint_name))
            except Exception as e:
                print(e)
        for field in model._meta.get_fields():
            is_index = schema_editor._field_should_be_indexed(
                model, field)
            if is_index:
                index_name = schema_editor._create_index_name(
                    real_model_name, [field.column])
                schema_editor.execute(schema_editor._delete_index_sql(
                    model, index_name))
        alter_statements = schema_editor.deferred_sql

    return alter_statements


class Insert:

    def __init__(self, data_file: DataFile, task_params=None):
        from .matches_mix import get_models_of_app, field_of_models_all
        self.task_params = task_params
        self.data_file = data_file
        self.file_control = data_file.petition_file_control.file_control
        self.agency = self.file_control.agency
        self.editable_models = get_models_of_app("med_cat")
        self.editable_models += get_models_of_app("formula")
        self.model_fields = {model["name"]: field_of_models_all(model)
                             for model in self.editable_models}

    # ########## FUNCIONES AUXILIARES #############
    def send_csv_to_db(self, table_file: TableFile):
        from task.serverless import async_in_lambda
        path = table_file.file.name
        model_name = table_file.collection.model_name
        # print("editable_models", self.editable_models)
        try:
            model_data = [model for model in self.editable_models
                          if model["model"] == model_name][0]
            snake_name = model_data["name"]
        except IndexError:
            print(f"MODELO: {model_name}")
            raise Exception("No se encontró el modelo en la lista de modelos")
        model_lower = model_name.lower()
        model_in_db = f"{model_data['app']}_{model_lower}"
        columns = self.model_fields[snake_name]
        field_names = [field["name"] for field in columns]
        columns_join = ", ".join(field_names)
        entity_optional_models = ["Diagnosis", "Medicament"]
        # "COPY temp_doctors (hash_id, full_name, medical_speciality, institution_id) FROM
        # '/path/to/input_doctors.csv' WITH (FORMAT CSV, HEADER)
        if model_data["app"] == "formula":
            # if settings.IS_LOCAL:
            query = self.build_copy_sql_aws(table_file, model_in_db, columns_join)
            sql_queries = [query]
        else:
            sql_queries = []
            temp_table = f"temp_{model_lower}"
            sql_queries.append(f"""
                CREATE TEMP TABLE {temp_table} AS SELECT * 
                FROM {model_in_db} WITH NO DATA;
            """)
            sql_queries.append(self.build_copy_sql_aws(
                table_file, temp_table, columns_join))
            optional_condition = ""
            if model_name not in entity_optional_models:
                entity_id = self.agency.entity_id
                optional_condition = f" AND {model_in_db}.entity_id = {entity_id} "
            # final_condition += f"{model_in_db}.hex_hash = {temp_table}.hex_hash"
            sql_queries.append(f"""
                INSERT INTO {model_in_db} ({columns_join})
                    SELECT {columns_join}
                    FROM {temp_table}
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {model_in_db} 
                        WHERE {model_in_db}.hex_hash = {temp_table}.hex_hash
                            {optional_condition}
                    );
            """)
        # desabasto_db = getattr(settings, "DATABASES", {}).get("default")
        desabasto_db = getattr(settings, "DATABASES", {}).get("default_prod")
        # save_csv_in_db(sql_query, desabasto_db)
        params = {
            "sql_queries": sql_queries,
            "db_config": desabasto_db,
            "table_file_id": table_file.id,
            "model_name": model_name,
        }
        self.task_params["models"] = [table_file.lap_sheet.sheet_file]
        self.task_params["function_after"] = "check_success_insert"
        print("MODELO: ----------- ", model_name.upper())
        return async_in_lambda("save_csv_in_db", params, self.task_params)

    def build_copy_sql_aws(self, table_file, model_in_db, columns_join):
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_location = getattr(settings, "AWS_LOCATION")
        region_name = getattr(settings, "AWS_S3_REGION_NAME")
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        path = table_file.file.name
        encoding = "LATIN1" if self.file_control.decode == "latin-1" else "UTF8"
        return f"""
            SELECT aws_s3.table_import_from_s3(
                '{model_in_db}',
                '{columns_join}',
                '(format csv, header true, delimiter "|", encoding "{encoding}")',
                '{bucket_name}',
                '{aws_location}/{path}',
                '{region_name}',
                '{access_key}',
                '{secret_key}'
            )
        """

    def build_copy_sql_local(self, table_file, model_in_db, columns_join):
        # from scripts.common import get_file, start_session
        # s3_client, dev_resource = start_session()
        # data = get_file(self, dev_resource).read()
        path = table_file.file.url
        # artificial_path = 'C:\\Users\\Ricardo\\Downloads\\diagnosis_3772_default_lap0.csv'
        artificial_path = 'diagnosis_3772_default_lap0.csv'
        # "COPY temp_doctors (hash_id, full_name, medical_speciality, institution_id) FROM
        # '/path/to/input_doctors.csv' WITH (FORMAT CSV, HEADER)
        encoding = "LATIN1" if self.file_control.decode == "latin-1" else "UTF8"
        return f"""
            COPY {model_in_db} ({columns_join})
            FROM '{artificial_path}'
            WITH (FORMAT CSV, HEADER, ENCODING {encoding})
        """
