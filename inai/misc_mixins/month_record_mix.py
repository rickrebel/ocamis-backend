from classify_task.models import Stage
from inai.models import MonthRecord
from task.serverless import async_in_lambda
from task.base_views import TaskBuilder
from task.main_views_aws import AwsFunction
from django.conf import settings
ocamis_db = getattr(settings, "DATABASES", {}).get("default")


class MonthRecordMix:

    # def __init__(self, month_record: MonthRecord, task_params=None):
    #     self.month_record = month_record
    #     self.task_params = task_params
    def __init__(self, month_record: MonthRecord,
                 task_params=None, base_task: AwsFunction = None):
        self.month_record = month_record
        self.task_params = task_params
        self.base_task = base_task

    def revert_stages(self, final_stage: Stage):
        from respond.models import TableFile
        from respond.models import LapSheet
        from respond.models import CrossingSheet
        from django.db import connection

        self.month_record.stage = final_stage
        if final_stage.name == "revert_stages":
            self.month_record.status_id = "finished"
        else:
            self.month_record.status_id = "created"

        self.month_record.last_validate = None
        self.month_record.last_indexing = None
        self.month_record.last_insertion = None
        # self.month_record.last_behavior = None

        self.month_record.error_process = None
        week_records = self.month_record.weeks.all()
        base_table_files = TableFile.objects.filter(
            week_record__month_record=self.month_record,
            collection__isnull=False)
        sheet_files = self.month_record.sheet_files.all()

        stage_pre_insert = Stage.objects.get(name="pre_insert")
        if final_stage.order <= stage_pre_insert.order:
            self.month_record.last_pre_insertion = None
            week_records.update(last_pre_insertion=None)

            related_lap_sheets = LapSheet.objects \
                .filter(sheet_file__in=sheet_files, lap=0)
            lap_missing_table_files = TableFile.objects.filter(
                lap_sheet__in=related_lap_sheets,
                collection__app_label="formula")
            lap_missing_table_files.update(inserted=False)

            related_lap_sheets.update(
                cat_inserted=False,
                missing_inserted=False)

            base_table_files.update(inserted=False)
            cursor = connection.cursor()
            formula_models = [
                "rx", "drug", "missingrow", "missingfield",
                "complementrx", "complementdrug", "diagnosisrx"]
            for table_name in formula_models:
                temp_table = f"tmp.fm_{self.month_record.temp_table}_{table_name}"
                cursor.execute(f"""
                    DROP TABLE IF EXISTS {temp_table} CASCADE;
                """)
            cursor.close()
            connection.commit()
            connection.close()

        stage_merge = Stage.objects.get(name="merge")
        if final_stage.order <= stage_merge.order:
            self.month_record.last_merge = None
            base_table_files.delete()
            week_records.update(
                last_merge=None)

        stage_analysis = Stage.objects.get(name="analysis")
        if final_stage.order <= stage_analysis.order:
            self.month_record.last_crossing = None
            lap_table_files = TableFile.objects.filter(
                week_record__month_record=self.month_record,
                lap_sheet__isnull=False)
            lap_table_files.update(
                rx_count=0,
                duplicates_count=0,
                shared_count=0)
            CrossingSheet.objects.filter(
                month_record=self.month_record).delete()
            week_records.update(
                rx_count=0,
                drugs_count=0,
                duplicates_count=0,
                shared_count=0,
                last_crossing=None,
                crosses=None)
            all_sheet_ids = self.month_record.sheet_files.all() \
                .values_list("id", flat=True)
            self.save_sums(all_sheet_ids)

        self.month_record.save()
        self.base_task.comprobate_status()

    def send_analysis(self):
        from respond.models import TableFile
        from data_param.models import FileControl

        # all_tasks = []
        insert_stage = Stage.objects.get(name="insert")
        if self.month_record.stage.order >= insert_stage.order:
            error = f"El mes {self.month_record.year_month} ya se insertó"
            return self.base_task.add_errors([error], http_response=True)
        all_table_files = TableFile.objects\
            .filter(
                week_record__month_record=self.month_record,
                collection__isnull=True,
            ).exclude(lap_sheet__sheet_file__behavior__is_discarded=True)

        laps = "petition_file_control__data_files__sheet_files__laps"
        months = "__table_files__week_record__month_record"
        filter_fc = {f"{laps}{months}": self.month_record}
        file_controls = FileControl.objects.filter(**filter_fc).distinct()
        unique_medicines = set()
        medicine_key = None
        for file_control in file_controls:
            medicine_field = file_control.columns\
                .filter(
                    final_field__is_unique=True,
                    final_field__collection__model_name="Medicament")\
                .order_by("-final_field__is_common", "final_field__name")\
                .first()
            if not medicine_field:
                error = "No se encontró campo de medicamento"
                return self.base_task.add_errors([error], http_response=True)
            unique_medicines.add(medicine_field.final_field_id)
        if len(unique_medicines) > 1:
            error = "Más de un campo de medicamento"
            return self.base_task.add_errors([error], http_response=True)
        elif len(unique_medicines) == 1:
            medicine_key = unique_medicines.pop()

        # week_base_task = TaskBuilder(
        # print("-x base_task.main_task", self.base_task.main_task)

        for week in self.month_record.weeks.all():
            # if week.last_crossing and week.last_transformation:
            #     if week.last_transformation < week.last_crossing:
            #         continue
            # init_data = WeekRecordSimpleSerializer(week).data
            # table_files = TableFile.objects.filter(
            #     week_record=week,
            #     collection__isnull=True)

            table_files = all_table_files.filter(week_record=week)
            file_names = list(table_files.values_list("file", flat=True))
            # Calculate if file_names has duplicates
            if len(file_names) != len(set(file_names)):
                # Calculate the first duplicate file
                first_duplicate_file = None
                for file_name in file_names:
                    if file_names.count(file_name) > 1:
                        first_duplicate_file = file_name
                        break
                error = f"Se están intentando enviar el mismo archivo " \
                        f"llamado {first_duplicate_file} más de una vez"
                return self.base_task.add_errors_and_raise([error])
            params = {
                "provider_id": week.provider_id,
                "table_files": file_names,
                "has_medicine_key": bool(medicine_key),
            }
            week_base_task = TaskBuilder(
                function_name="analyze_uniques",
                parent_class=self.base_task, model_obj=week,
                function_after="analyze_uniques_after",
                params=params, models=[week, self.month_record])
            # print("week_base_task", week_base_task)

            # self.task_params["models"] = [week, self.month_record]
            # self.task_params["function_after"] = "analyze_uniques_after"
            # self.base_task.models = [week, self.month_record]
            # RICK TASK: No estoy seguro de dejar esto así comentado
            # params_after = self.task_params.get("params_after", {})
            # self.task_params["params_after"] = params_after
            # async_task = async_in_lambda(
            #     "analyze_uniques", params, self.task_params)
            week_base_task.async_in_lambda(comprobate=False)
            # all_tasks.append(async_task)
            # if self.month_record.provider.split_by_delegation:
            #     time.sleep(0.2)
        # return all_tasks, [], True

    def merge_files_by_week(self):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile
        from django.utils import timezone
        from django.db.models import F

        # related_sheet_files = self.month_record.sheet_files.all()

        my_insert = InsertMonth(self.month_record, self.task_params,
                                base_task=self.base_task)
        # new_tasks = []
        week_records = self.month_record.weeks.all().prefetch_related(
            "table_files", "table_files__collection", "table_files__lap_sheet",
            "table_files__lap_sheet__sheet_file")

        all_table_files = TableFile.objects \
            .filter(
                week_record__month_record=self.month_record,
                lap_sheet__lap=0)\
            .exclude(lap_sheet__sheet_file__behavior__is_discarded=True)\
            .values(
                "week_record_id", "id", "file", "collection", "year",
                "month", "year_month", "iso_week", "iso_year", "year_week",
                "lap_sheet__sheet_file__behavior_id"
            ).annotate(
                sheet_behavior=F("lap_sheet__sheet_file__behavior_id"))

        for wr in week_records:
            # if ew.last_merge:
            #     if ew.last_transformation < ew.last_crossing < ew.last_merge:
            #         continue
            # if self.month_record.provider_id == 55 and ew.complete:
            #     continue
            # lap_sheet.sheet_file.behavior_id
            # week_base_table_files = ew.table_files\
            #     .filter(lap_sheet__lap=0)\
            #     .prefetch_related("lap_sheet__sheet_file")
            week_base_table_files = list(all_table_files.filter(
                week_record_id=wr.id))
            # if week_base_table_files.count() == 0:
            if not week_base_table_files:
                wr.last_merge = timezone.now()
                wr.save()
                continue
            my_insert.merge_week_base_tables(wr, week_base_table_files)
            # new_tasks.append(table_task)

        # return new_tasks, [], True

    def pre_insert_month(self):
        from django.db import connection
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile
        from respond.models import LapSheet

        # CREATE TABLE fm_55_201902_rx (LIKE formula_rx INCLUDING CONSTRAINTS);
        # CREATE TABLE fm_55_201902_drug (LIKE formula_drug INCLUDING CONSTRAINTS);
        queries = {"create": [], "drop": []}

        drug_table = f"fm_{self.month_record.temp_table}_drug"
        cursor = connection.cursor()
        exists_temp_tables = exist_temp_table(drug_table, "tmp")

        formula_tables = ["rx", "drug", "missingrow", "missingfield",
                          "complementrx", "complementdrug", "diagnosisrx"]
        for table_name in formula_tables:
            temp_table = f"tmp.fm_{self.month_record.temp_table}_{table_name}"
            queries["create"].append(f"""
                CREATE TABLE {temp_table}
                (LIKE public.formula_{table_name} INCLUDING CONSTRAINTS);
            """)
            queries["drop"].append(f"""
                DROP TABLE IF EXISTS {temp_table} CASCADE; 
            """)
        # for operation in ["create", "drop"]:
        if not exists_temp_tables:
            for query in queries["create"]:
                cursor.execute(query)
        cursor.close()

        month_table_files = TableFile.objects\
            .filter(
                week_record__month_record=self.month_record,
                collection__isnull=True
            )\
            .exclude(inserted=True)
        related_sheet_files = self.month_record.sheet_files.all()

        related_lap_sheets = LapSheet.objects\
            .filter(sheet_file__in=related_sheet_files)\
            .exclude(sheet_file__behavior__is_discarded=True)

        pending_lap_sheets = related_lap_sheets.filter(
            cat_inserted=False, lap=0)

        collection_table_files = TableFile.objects.filter(
            lap_sheet__in=pending_lap_sheets,
            collection__app_label="med_cat",
            inserted=False)
        errors = []
        if not collection_table_files.exists() and not month_table_files.exists():
            error = ["No existen tablas por insertar para el mes "
                     f"{self.month_record.year_month}"]
            errors.append(error)
            # return [], errors, False
        if errors:
            print("error", errors)

        # self.task_params["keep_tasks"] = True
        # task_cats, task_params_cat = build_task_params(
        #     self.month_record, 'save_month_cat_tables', **self.task_params)
        # new_tasks = []
        # errors = []
        # cat_tasks = []
        cats_task = TaskBuilder(
            function_name="save_month_cat_tables", keep_tasks=True,
            parent_class=self.base_task, model_obj=self.month_record)

        # new_tasks.append(task_cats)
        my_insert_cat = InsertMonth(self.month_record, base_task=cats_task)

        for lap_sheet in pending_lap_sheets:
            current_table_files = collection_table_files.filter(
                lap_sheet=lap_sheet,
                collection__app_label="med_cat",
                inserted=False)
            if not current_table_files.exists():
                continue
            my_insert_cat.send_lap_tables_to_db(
                lap_sheet, current_table_files, "cat_inserted")
            # cat_tasks.append(new_task)
            # new_tasks.append(new_task)

        # if not cat_tasks:
        #     comprobate_status(task_cats)
        if not cats_task.new_tasks:
            cats_task.comprobate_status()

        missing_table_files = TableFile.objects.filter(
            lap_sheet__in=related_lap_sheets,
            collection__app_label="formula",
            inserted=False)
        # base_table_files = TableFile.objects.filter(
        #     lap_sheet__isnull=True,
        #     year_month=self.month_record.year_month,
        #     collection__app_label="formula",
        #     inserted=False)

        # task_base, task_params_base = build_task_params(
        #     self.month_record, 'save_month_base_tables', **self.task_params)
        formula_task = TaskBuilder(
            function_name="save_month_base_tables", keep_tasks=True,
            model_obj=self.month_record, parent_class=self.base_task)
        # new_tasks.append(task_base)
        # my_insert_base = InsertMonth(self.month_record, task_params_base)
        my_insert_base = InsertMonth(self.month_record, base_task=formula_task)
        # base_tasks = []
        for week in self.month_record.weeks.all():
            week_base_table_files = week.table_files.filter(
                lap_sheet__isnull=True,
                collection__app_label="formula",
                inserted=False)
            if not week_base_table_files.exists():
                continue
            my_insert_base.send_base_tables_to_db(week, week_base_table_files)
            # base_tasks.append(week_task)
            # new_tasks.append(week_task)
        # if not base_tasks:
        #     comprobate_status(task_base)
        if not formula_task.new_tasks:
            formula_task.comprobate_status()

        for lap_sheet in related_lap_sheets:
            lap_missing_tables = missing_table_files.filter(
                lap_sheet=lap_sheet)
            if not lap_missing_tables:
                lap_sheet.missing_inserted = True
                # lap_sheet.sheet_file.save_stage('insert', [])
            else:
                my_insert_base.send_lap_tables_to_db(
                    lap_sheet, lap_missing_tables, "missing_inserted")
                # new_tasks.append(new_task)
        # return new_tasks, errors, True

    def validate_month(self):
        from respond.models import TableFile
        clean_queries = []

        self.check_temp_tables()

        error_process_str = self.get_error_process_str()
        if error_process_str:
            if "semanas con más medicamentos" in error_process_str:
                models = {
                    "rx": "uuid_folio",
                    "drug": "uuid",
                }
                for table_name, field in models.items():
                    temp_table = f"tmp.fm_{self.month_record.temp_table}_{table_name}"
                    clean_queries.append(f"""
                        DELETE FROM {temp_table}
                        WHERE {field} IN (
                            SELECT {field}
                            FROM (
                                SELECT {field}, ROW_NUMBER() OVER (
                                    PARTITION BY {field}
                                    ORDER BY {field}) AS rnum
                                FROM {temp_table}
                            ) t
                            WHERE t.rnum > 1
                        );
                    """)
            elif "blocked by process " not in error_process_str:
                errors = [f"Existen otros errores: {error_process_str}"]
                self.month_record.save_error_process(errors)
                return self.base_task.add_errors(errors, http_response=True)

        drugs_counts = TableFile.objects.filter(
                week_record__month_record=self.month_record,
                collection__model_name="Drug")\
            .values("week_record_id", "drugs_count")
        # drugs_counts = {d["id"]: d["drugs_count"] for d in drugs_counts}
        drugs_counts = list(drugs_counts)
        drugs_object = {}
        for drug in drugs_counts:
            drugs_object[drug["week_record_id"]] = drug["drugs_count"]
        if not drugs_object:
            errors = ["No se encontraron semanas con medicamentos"]
            self.month_record.save_error_process(errors)
            self.base_task.add_errors(errors, http_response=True)
        temp_drug = f"tmp.fm_{self.month_record.temp_table}_drug"
        count_query = f"""
            SELECT week_record_id,
            COUNT(*)
            FROM {temp_drug}
            GROUP BY week_record_id;
        """

        last_query = f"""
            UPDATE public.inai_entitymonth
            SET last_validate = now()
            WHERE id = {self.month_record.id}
        """

        params = {
            "month_record_id": self.month_record.id,
            "temp_table": self.month_record.temp_table,
            "db_config": ocamis_db,
            "clean_queries": clean_queries,
            "count_query": count_query,
            "drugs_object": drugs_object,
            "last_query": last_query,
        }

        # all_tasks = []
        # self.task_params["models"] = [self.month_record]
        # async_task = async_in_lambda(
        #     "validate_temp_tables", params, self.task_params)
        # if async_task:
        #     all_tasks.append(async_task)
        validate_task = TaskBuilder(
            function_name="validate_temp_tables", params=params,
            parent_class=self.base_task, model_obj=self.month_record)
        validate_task.async_in_lambda(comprobate=False)
        # return all_tasks, errors, True

    def indexing_month(self):
        from formula.views import modify_constraints
        # errors = []

        self.check_temp_tables()

        error_process_str = self.get_error_process_str()
        if error_process_str:
            error = f"Existen otros errores: {error_process_str}"
            self.month_record.save_error_process([error])
            self.base_task.add_errors([error], http_response=True)

        constraint_queries = modify_constraints(
            True, False, self.month_record.temp_table)

        last_query = f"""
            UPDATE public.inai_entitymonth
            SET last_indexing = now()
            WHERE id = {self.month_record.id}
        """

        params = {
            "month_record_id": self.month_record.id,
            "temp_table": self.month_record.temp_table,
            "db_config": ocamis_db,
            "constraint_queries": constraint_queries,
            "last_query": last_query,
        }

        # all_tasks = []
        # self.task_params["models"] = [self.month_record]
        # async_task = async_in_lambda(
        #     "indexing_temp_tables", params, self.task_params)
        # if async_task:
        #     all_tasks.append(async_task)
        indexing_task = TaskBuilder(
            function_name="indexing_temp_tables", params=params,
            parent_class=self.base_task, model_obj=self.month_record)
        indexing_task.async_in_lambda(comprobate=False)
        # return all_tasks, errors, True

    def final_insert_month(self):
        errors = []

        # counts_object = {}
        # for table_file in table_files:
        #     counts_object[table_file["id"]] = table_file["drugs_count"]
        create_base_tables = []
        insert_queries = []
        drop_queries = []
        try:
            base_table = self.month_record.cluster.name
        except Exception as e:
            error = f"El proveedor no está asociado a ningún cluster:"
            self.base_task.add_errors([error], http_response=True)
        formula_tables = ["rx", "drug", "missingrow", "missingfield",
                          "complementrx", "complementdrug", "diagnosisrx"]
        self.check_temp_tables()
        for table_name in formula_tables:
            temp_table = f"fm_{self.month_record.temp_table}_{table_name}"
            exists_temp_tables = exist_temp_table(temp_table, "tmp")
            if not exists_temp_tables:
                continue
            base_table_name = f"frm_{base_table}_{table_name}"
            exists_base_table = exist_temp_table(base_table_name, "base")
            if not exists_base_table:
                create_base_tables.append(f"""
                    CREATE TABLE base.{base_table_name}
                    (LIKE public.formula_{table_name} INCLUDING CONSTRAINTS);
                """)
            insert_queries.append(f"""
                INSERT INTO base.{base_table_name}
                SELECT *
                FROM tmp.{temp_table};
            """)
            drop_queries.append(f"""
                DROP TABLE IF EXISTS {temp_table} CASCADE;
            """)

        first_query = f"""
            SELECT last_insertion IS NOT NULL AS last_insertion
            FROM public.inai_entitymonth
            WHERE id = {self.month_record.id}
        """
        last_query = f"""
            UPDATE public.inai_entitymonth
            SET last_insertion = now()
            WHERE id = {self.month_record.id}
        """

        params = {
            "month_record_id": self.month_record.id,
            "temp_table": self.month_record.temp_table,
            "db_config": ocamis_db,
            "create_base_tables": create_base_tables,
            "first_query": first_query,
            "insert_queries": insert_queries,
            "drop_queries": drop_queries,
            "last_query": last_query,
        }
        # all_tasks = []
        # self.task_params["models"] = [self.month_record]
        # async_task = async_in_lambda(
        #     "insert_temp_tables", params, self.task_params)
        # if async_task:
        #     all_tasks.append(async_task)
        insert_task = TaskBuilder(
            function_name="insert_temp_tables", params=params,
            parent_class=self.base_task, model_obj=self.month_record)
        insert_task.async_in_lambda(comprobate=False)
        # return all_tasks, [], True

    def save_sums(self, all_sheet_ids):
        from respond.models import LapSheet
        from django.db.models import Sum

        sum_fields = [
            "drugs_count", "rx_count", "duplicates_count", "shared_count"]
        query_sheet_sums = [Sum(field) for field in sum_fields]
        # query_annotations = {field: Sum(field) for field in sum_fields}
        all_laps = LapSheet.objects.filter(
            sheet_file_id__in=all_sheet_ids, lap=0)
        for lap_sheet in all_laps:
            table_sums = lap_sheet.table_files.aggregate(*query_sheet_sums)
            for field in sum_fields:
                setattr(lap_sheet.sheet_file, field,
                        table_sums[f"{field}__sum"] or 0)
            lap_sheet.sheet_file.save()

        query_sums = [Sum(field) for field in sum_fields]
        result_sums = self.month_record.weeks.all().aggregate(*query_sums)
        # print("result_sums", result_sums)
        for field in sum_fields:
            setattr(self.month_record, field,
                    result_sums[f"{field}__sum"] or 0)

    def get_error_process_str(self):
        if not self.month_record.error_process:
            return ""
        error_process_list = self.month_record.error_process
        return "\n".join(error_process_list)

    def check_temp_tables(self):
        errors = []
        for table_name in ["rx", "drug"]:
            temp_table = f"fm_{self.month_record.temp_table}_{table_name}"
            exists_temp_tables = exist_temp_table(temp_table, "tmp")
            if not exists_temp_tables:
                error = f"No existe la tabla esencial {temp_table}"
                errors.append(error)
        if errors:
            self.month_record.status_id = "with_errors"
            self.month_record.save()
            self.base_task.add_errors(errors, http_response=True)


def exist_temp_table(table_name, schema="public"):
    from django.db import connection
    query_if_exists = f"""
        SELECT EXISTS(
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = '{table_name}' AND n.nspname = '{schema}'
        );
    """
    cursor = connection.cursor()
    cursor.execute(query_if_exists)
    exists_temp_tables = cursor.fetchone()[0]
    cursor.close()
    return exists_temp_tables
