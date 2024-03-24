from django.conf import settings
from inai.models import EntityMonth, EntityWeek
from respond.models import LapSheet
from task.serverless import async_in_lambda

ocamis_db = getattr(settings, "DATABASES", {}).get("default")


def build_copy_sql_aws(path, model_in_db, columns_join):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    region_name = getattr(settings, "AWS_S3_REGION_NAME")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    return f"""
        SELECT aws_s3.table_import_from_s3(
            '{model_in_db}',
            '{columns_join}',
            '(format csv, header true, delimiter "|", encoding "UTF8")',
            '{bucket_name}',
            '{aws_location}/{path}',
            '{region_name}',
            '{access_key}',
            '{secret_key}'
        )
    """


def build_alternative_query(model_in_db, columns_join):
    return f"""
        INSERT INTO {model_in_db} ({columns_join})
        VALUES (LIST_VALUES);
    """


class InsertMonth:

    def __init__(self, entity_month: EntityMonth, task_params=None):
        from respond.data_file_mixins.matches_mix import (
            get_models_of_app, field_of_models)
        self.task_params = task_params
        self.entity_month = entity_month
        self.entity = self.entity_month.entity
        self.editable_models = get_models_of_app("med_cat")
        self.editable_models += get_models_of_app("formula")
        self.model_fields = {model["model"]: field_of_models(model)
                             for model in self.editable_models}
        self.models_data = {}
        for model in self.editable_models:
            model_name = model["model"]
            columns = self.model_fields[model_name]
            field_names = [field["name"] for field in columns]
            self.models_data[model_name] = {
                "model_in_db": model["model_in_db"],
                "model_name": model_name,
                "columns_join": ", ".join(field_names),
                "app": model["app"],
            }
        self.base_models_names = ["Drug", "Rx"]
        self.normal_models = [model for model in self.editable_models
                              if model["model"] not in self.base_models_names]
        self.base_models = [model for model in self.editable_models
                            if model["model"] in self.base_models_names]

    def merge_week_base_tables(self, entity_week: EntityWeek, week_table_files: list):
        fields_in_name = ["iso_year", "iso_week", "year", "month"]
        complement_name = "_".join([str(getattr(entity_week, field))
                                    for field in fields_in_name])
        iso_delegation = entity_week.iso_delegation.id if \
            entity_week.iso_delegation else 0
        only_name = (
            f"NEW_ELEM_NAME/NEW_ELEM_NAME_by_week_{complement_name}_"
            f"{str(iso_delegation)}.csv")
        entity_type = self.entity.entity_type[:8].lower()
        acronym = self.entity.acronym.lower()
        final_path = "/".join([entity_type, acronym, only_name])
        params = {
            # "week_table_files": TableFileAwsSerializer(
            #     week_table_files, many=True).data,
            "week_table_files": week_table_files,
            "final_path": final_path,
            "entity_week_id": entity_week.id,
        }
        current_task_params = self.task_params.copy()
        current_task_params["models"] = [entity_week, self.entity_month]
        current_task_params["entity_week_id"] = entity_week.id
        current_task_params["function_after"] = "save_merged_from_aws"
        return async_in_lambda("build_week_csvs", params, current_task_params)

    def build_query_tables(self, table_files, complement=None):
        queries_by_model = {}
        for table_file in table_files:
            model_name = table_file.collection.model_name
            try:
                model_data = self.models_data[model_name]
            except KeyError:
                print(f"MODELO: {model_name}")
                raise Exception(
                    "No se encontró el modelo en la lista de modelos")
            path = table_file.file.name
            if model_name not in queries_by_model:
                columns_join = model_data["columns_join"]
                model_in_db = model_data["model_in_db"]
                if model_data["app"] == "formula":
                    if complement:
                        model_in_db = model_in_db.replace(
                            "formula_", f"fm_{complement}_")
                    query_base = build_copy_sql_aws(
                        "PATH_URL", model_in_db, columns_join)
                    alternative_query = build_alternative_query(
                        model_in_db, columns_join)
                    queries_by_model[model_name] = {
                        "base_queries": [query_base],
                        "alternative_query": alternative_query,
                        "files": [],
                    }
                else:
                    base_queries = self.build_catalog_queries(
                        "PATH_URL", columns_join, model_in_db, model_name)
                    alternative_query = build_alternative_query(
                        model_in_db, columns_join)
                    queries_by_model[model_name] = {
                        "base_queries": base_queries,
                        "alternative_query": alternative_query,
                        "files": [],
                    }
            queries_by_model[model_name]["files"].append(path)
        return queries_by_model

    def send_base_tables_to_db(
            self, entity_week: EntityWeek, table_files: list):
        first_query = f"""
            SELECT last_pre_insertion IS NOT NULL AS last_pre_insertion
            FROM public.inai_entityweek
            WHERE id = {entity_week.id}
        """
        last_query = f"""
            UPDATE public.inai_entityweek
            SET last_pre_insertion = now()
            WHERE id = {entity_week.id}
        """
        temp_complement = self.entity_month.temp_table
        main_queries = self.build_query_tables(table_files, temp_complement)
        table_files_ids = [table_file.id for table_file in table_files]
        params = {
            "first_query": first_query,
            "last_query": last_query,
            "queries_by_model": main_queries,
            "db_config": ocamis_db,
            "entity_month_id": self.entity_month.id,
            "entity_week_id": entity_week.id,
            "table_files_ids": table_files_ids,
        }
        # self.task_params["function_after"] = "check_success_insert"
        current_task_params = self.task_params.copy()
        current_task_params["models"] = [entity_week, self.entity_month]
        # current_task_params["params_after"] = {
        #     "table_files_ids": [table_file.id for table_file in table_files],
        # }
        # return async_in_lambda("save_csv_in_db", params, current_task_params)
        return async_in_lambda(
            "save_week_base_models", params, current_task_params)

    def send_lap_tables_to_db(
            self, lap_sheet: LapSheet, table_files: list, inserted_field):
        first_query = f"""
            SELECT {inserted_field}
            FROM public.inai_lapsheet
            WHERE id = {lap_sheet.id}
        """
        last_query = f"""
            UPDATE public.inai_lapsheet
            SET {inserted_field} = true
            WHERE id = {lap_sheet.id}
        """

        current_task_params = self.task_params.copy()
        current_task_params["models"] = [
            lap_sheet.sheet_file,
            lap_sheet.sheet_file.data_file,
            self.entity_month]
        if inserted_field == "missing_inserted":
            function_name = "save_lap_missing_tables"
            temp_complement = self.entity_month.temp_table
            current_task_params["function_after"] = "check_success_insert"
            current_task_params["subgroup"] = "missing"
        elif inserted_field == "cat_inserted":
            function_name = "save_lap_cat_tables"
            temp_complement = None
            current_task_params["subgroup"] = "med_cat"
        else:
            raise Exception("No se encontró el campo de inserción")
        table_files_ids = [table_file.id for table_file in table_files]
        # current_task_params["params_after"] = {
        #     "table_files_ids": [table_file.id for table_file in table_files],
        # }
        params = {
            "first_query": first_query,
            "last_query": last_query,
            "queries_by_model": self.build_query_tables(table_files, temp_complement),
            "db_config": ocamis_db,
            "lap_sheet_id": lap_sheet.id,
            "table_files_ids": table_files_ids,
        }
        # return async_in_lambda("save_csv_in_db", params, current_task_params)
        return async_in_lambda(function_name, params, current_task_params)

    def build_catalog_queries(
            self, path, columns_join, model_in_db, model_name):
        entity_optional_models = ["Diagnosis", "Medicament"]
        sql_queries = []
        temp_table = f"temp_{model_in_db}"
        sql_queries.append(f"""
            CREATE TEMP TABLE {temp_table} AS SELECT * 
            FROM {model_in_db} WITH NO DATA;
        """)
        sql_queries.append(build_copy_sql_aws(
            path, temp_table, columns_join))
        optional_condition = ""
        if model_name not in entity_optional_models:
            entity_id = self.entity.id
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
        sql_queries.append(f"""
            DROP TABLE {temp_table};
        """)
        return sql_queries
