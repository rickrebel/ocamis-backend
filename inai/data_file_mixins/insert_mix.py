from django.conf import settings
from django.db import connection
from inai.models import DataFile, LapSheet
from task.models import Platform


def build_copy_sql_aws(table_file, model_in_db, columns_join):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    region_name = getattr(settings, "AWS_S3_REGION_NAME")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    path = table_file.file.name
    # encoding = "LATIN1" if self.file_control.decode == "latin-1" else "UTF8"
    encoding = "UTF8"
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


def rebuild_primary_key(cursor, table_name, constraint):
    from inai.models import EntityWeek
    from task.models import AsyncTask
    from task.serverless import execute_async
    fields = [
        "entity_id", "iso_year", "month", "iso_week", "iso_delegation",
        "month", "year"]
    try:
        cursor.execute(constraint)
    except Exception as e:
        str_e = str(e)
        # Key (uuid_folio)=(d0c82080-f73e-4cf7-9e65-557c6ecfa64b) is duplicated.
        if "is duplicated" in str_e and "Key (uuid_folio)" in str_e:
            value = str_e.split("Key (uuid_folio)=")[1].split(")")[0]
            print("value", value)

            query_duplicates = f"""
                SELECT {", ".join(fields)} 
                 FROM {table_name} WHERE uuid_folio = '{value}'
            """
            cursor.execute(query_duplicates)
            result = cursor.fetchone()
            get_params = {field: result[i] for i, field in enumerate(fields)}
            entity_week = EntityWeek.objects.get(**get_params)
            print("entity_week", entity_week)
            complement_delete_rx = [f"{field} = {result[i]}"
                                    for i, field in enumerate(fields)]
            query_delete_rx = f"""
                DELETE FROM formula_rx WHERE {", ".join(complement_delete_rx)}
            """
            print("query_delete_rx", query_delete_rx)
            cursor.execute(query_delete_rx)
            complement_delete_drug = f"""
                DELETE FROM formula_drug WHERE entity_week_id = {entity_week.id}
            """
            print("complement_delete_drug", complement_delete_drug)
            cursor.execute(complement_delete_drug)
            # last_insertion = entity_week.last_insertion
            entity_week.last_insertion = None
            entity_week.save()
            task = AsyncTask.objects.filter(
                entity_week=entity_week, task_function_id='save_csv_in_db')
            if task.exists():
                next_task = task.first()
                execute_async(next_task, next_task.original_request)
            rebuild_primary_key(cursor, table_name, constraint)
        else:
            raise e


def modify_constraints(is_create=True, is_rebuild=False):
    from scripts.ocamis_verified.constrains import get_constraints
    from datetime import datetime
    create_constrains, delete_constrains = get_constraints(is_rebuild)
    if is_rebuild:
        return
    with_change = False
    cursor = connection.cursor()
    print("START", datetime.now())

    if is_create:  # and not platform.has_constrains:
        print("create_constrains")
        with_change = True
        for constraint in create_constrains:
            try:
                print(">>>>> time:", datetime.now())
                print("constraint", constraint)
                if "formula_rx_pkey" in constraint:
                    rebuild_primary_key(cursor, "formula_rx", constraint)
                else:
                    cursor.execute(constraint)
                print("--------------------------")
            except Exception as e:
                str_e = str(e)
                if "already exists" in str_e:
                    continue
                if "multiple primary keys" in str_e:
                    continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                raise e
    elif not is_create:  # and platform.has_constrains:
        print("delete_constrains")
        with_change = True
        for constraint in reversed(delete_constrains):
            print("constraint", constraint)
            cursor.execute(constraint)
    # connection.commit()
    print("FINAL", datetime.now())
    cursor.close()
    connection.close()
    if with_change:
        Platform.objects.all().update(has_constrains=is_create)


class Insert:

    def __init__(self, data_file: DataFile, task_params=None):
        from .matches_mix import get_models_of_app, field_of_models
        self.task_params = task_params
        self.data_file = data_file
        self.file_control = data_file.petition_file_control.file_control
        self.agency = self.file_control.agency
        self.editable_models = get_models_of_app("med_cat")
        self.editable_models += get_models_of_app("formula")
        self.model_fields = {model["name"]: field_of_models(model)
                             for model in self.editable_models}

    # def send_csv_to_db(self, table_file: TableFile):
    def send_csv_to_db(self, lap_sheet: LapSheet):
        from task.serverless import async_in_lambda
        table_files = lap_sheet.table_files.all()
        first_query = f"""
            SELECT inserted
            FROM public.inai_lapsheet
            WHERE id = {lap_sheet.id}
        """
        all_queries = []
        for table_file in table_files:
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
            # "COPY temp_doctors (hash_id, full_name, medical_speciality, institution_id) FROM
            # '/path/to/input_doctors.csv' WITH (FORMAT CSV, HEADER)
            platform = Platform.objects.all().last()
            if not platform:
                platform = Platform.objects.create(version="2.3")
            if platform.has_constrains:
                modify_constraints(is_create=False)
            if model_data["app"] == "formula":
                # if settings.IS_LOCAL:
                query = build_copy_sql_aws(
                    table_file, model_in_db, columns_join)
                # sql_queries = [query]
                all_queries.append(query)
            else:
                sql_queries = self.build_catalog_queries(
                    table_file, columns_join, model_in_db, model_name)
                all_queries += sql_queries
        last_query = f"""
            UPDATE public.inai_lapsheet
            SET inserted = true
            WHERE id = {lap_sheet.id}
        """
        all_queries.append(last_query)
        desabasto_db = getattr(settings, "DATABASES", {}).get("default_prod")
        if not desabasto_db:
            desabasto_db = getattr(settings, "DATABASES", {}).get("default")
        # save_csv_in_db(sql_query, desabasto_db)
        params = {
            "first_query": first_query,
            "sql_queries": all_queries,
            "db_config": desabasto_db,
            # "table_file_id": table_file.id,
            "lap_sheet_id": lap_sheet.id,
            # "model_name": model_name,
        }
        self.task_params["models"] = [
            lap_sheet.sheet_file, lap_sheet.sheet_file.data_file]
        self.task_params["function_after"] = "check_success_insert"
        # print("MODELO: ----------- ", model_name.upper())
        return async_in_lambda("save_csv_in_db", params, self.task_params)

    def build_catalog_queries(
            self, table_file, columns_join, model_in_db, model_name):
        entity_optional_models = ["Diagnosis", "Medicament"]
        sql_queries = []
        temp_table = f"temp_{model_in_db}"
        sql_queries.append(f"""
            CREATE TEMP TABLE {temp_table} AS SELECT * 
            FROM {model_in_db} WITH NO DATA;
        """)
        sql_queries.append(build_copy_sql_aws(
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
        return sql_queries

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
