from django.conf import settings
from inai.models import MonthRecord, WeekRecord
from respond.models import LapSheet
from data_param.models import Collection
# from task.serverless import async_in_lambda
from task.builder import TaskBuilder

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

    def __init__(self, month_record: MonthRecord, base_task: TaskBuilder = None):
        from respond.data_file_mixins.matches_mix import (
            get_models_of_app, field_of_models)
        self.month_record = month_record
        self.provider = self.month_record.provider
        editable_models = get_models_of_app("med_cat")
        editable_models += get_models_of_app("formula")
        model_fields = {model["model"]: field_of_models(model)
                        for model in editable_models}
        self.models_data = {}
        for model in editable_models:
            model_name = model["model"]
            columns = model_fields[model_name]
            field_names = [field["name"] for field in columns]
            self.models_data[model_name] = {
                "model_in_db": model["model_in_db"],
                "model_name": model_name,
                "columns_join": ", ".join(field_names),
                "app": model["app"],
            }
        self.base_task = base_task
        self.collection_table_files = None

    def merge_week_base_tables(
            self, week_record: WeekRecord, week_table_files: list):
        from respond.models import get_elems_by_provider, join_path
        fields_in_name = ["iso_year", "iso_week", "year", "month"]
        complement_name = "_".join([str(getattr(week_record, field))
                                    for field in fields_in_name])
        iso_delegation = week_record.iso_delegation.id if \
            week_record.iso_delegation else 0
        only_name = (
            f"NEW_ELEM_NAME/NEW_ELEM_NAME_by_week_{complement_name}_"
            f"{str(iso_delegation)}.csv")
        elems = get_elems_by_provider(self.provider, "merged_tables")
        elems.append(str(week_record.year))
        # provider_type = self.provider.provider_type[:8].lower()
        # acronym = self.provider.acronym.lower()
        # final_path = "/".join([provider_type, acronym, only_name])
        params = {
            "week_table_files": week_table_files,
            "final_path": join_path(elems, only_name),
            "week_record_id": week_record.id,
            "provider_id": self.provider.id,
        }
        week_task = TaskBuilder(
            "build_week_csvs", parent_class=self.base_task,
            params=params, models=[week_record, self.month_record],
            function_after="save_merged_from_aws")
        return week_task.async_in_lambda()

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
                            "formula_", f"tmp.fm_{complement}_")
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
                        "PATH_URL", columns_join, model_in_db)
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
            self, week_record: WeekRecord, table_files: list):

        params = {
            "db_config": ocamis_db,
            "week_record_id": week_record.id,
            "month_record_id": self.month_record.id,
            "first_query": f"""
                SELECT last_pre_insertion IS NOT NULL AS last_pre_insertion
                FROM public.inai_entityweek
                WHERE id = {week_record.id}
            """,
            "last_query": f"""
                UPDATE public.inai_entityweek
                SET last_pre_insertion = now()
                WHERE id = {week_record.id}
            """
        }
        temp_complement = self.month_record.temp_table
        main_queries = self.build_query_tables(table_files, temp_complement)
        table_files_ids = [table_file.id for table_file in table_files]
        params["queries_by_model"] = list(main_queries.values())
        params["table_files_ids"] = table_files_ids
        week_task = TaskBuilder(
            "save_week_base_models", parent_class=self.base_task,
            params=params, models=[week_record, self.month_record])
        return week_task.async_in_lambda()

    def send_cat_tables_to_db(self):
        from respond.models import TableFile
        self.collection_table_files = TableFile.objects.filter(
            lap_sheet__cat_inserted=False, lap_sheet__lap=0,
            lap_sheet__sheet_file__month_records__in=[self.month_record],
            lap_sheet__sheet_file__behavior__is_discarded=False,
            collection__app_label="med_cat", inserted=False)

        collection_ids = self.collection_table_files.values_list(
            "collection", flat=True).distinct()
        unique_collections = set(collection_ids)
        collections = Collection.objects.filter(id__in=unique_collections)
        for collection in collections:
            self.insert_collection(collection)

    def insert_collection(self, collection: Collection):

        table_files = self.collection_table_files\
            .filter(collection=collection)
        model_name = collection.model_name
        model_data = self.models_data[model_name]
        table_files_ids = [table_file.id for table_file in table_files]
        paths = [table_file.file.name for table_file in table_files]

        params = {
            "db_config": ocamis_db,
            "model_in_db": model_data["model_in_db"],
            "columns_join": model_data["columns_join"],
            "table_files_ids": table_files_ids,
            "table_files_paths": paths,
            "month_record_id": self.month_record.id,
        }
        collection_task = TaskBuilder(
            "save_cat_tables", parent_class=self.base_task,
            params=params, models=[self.month_record], keep_tasks=True,
            subgroup=model_name)
        collection_task.async_in_lambda()

    def send_lap_tables_to_db(self, lap_sheet: LapSheet, table_files: list):
        params = {
            "db_config": ocamis_db,
            "lap_sheet_id": lap_sheet.id,
            "first_query": f"""
                SELECT missing_inserted
                FROM public.inai_lapsheet
                WHERE id = {lap_sheet.id}
            """,
            "last_query": f"""
                UPDATE public.inai_lapsheet
                SET missing_inserted = true
                WHERE id = {lap_sheet.id}
            """
        }

        temp_complement = self.month_record.temp_table
        main_queries = self.build_query_tables(table_files, temp_complement)
        table_files_ids = [table_file.id for table_file in table_files]
        params["queries_by_model"] = list(main_queries.values())
        params["table_files_ids"] = table_files_ids
        models = [lap_sheet.sheet_file,
                  lap_sheet.sheet_file.data_file, self.month_record]
        lap_task = TaskBuilder(
            "save_lap_missing_tables", parent_class=self.base_task,
            params=params, models=models, keep_tasks=True,
            function_after="check_success_insert", subgroup="missing")
        lap_task.async_in_lambda()

    def build_catalog_queries(self, path, columns_join, model_in_db):
        sql_queries = []
        temp_table = f"temp_{model_in_db}"
        sql_queries.append(f"""
            CREATE TEMP TABLE {temp_table} AS SELECT * 
            FROM {model_in_db} WITH NO DATA;
        """)
        sql_queries.append(build_copy_sql_aws(
            path, temp_table, columns_join))
        sql_queries.append(f"""
            INSERT INTO {model_in_db} ({columns_join})
                SELECT {columns_join}
                FROM {temp_table}
                WHERE NOT EXISTS (
                    SELECT 1 FROM {model_in_db} 
                    WHERE {model_in_db}.hex_hash = {temp_table}.hex_hash
                );
        """)
        sql_queries.append(f"""
            DROP TABLE {temp_table};
        """)
        return sql_queries
