from classify_task.models import Stage
from inai.models import MonthRecord
from task.serverless import async_in_lambda
from django.conf import settings
ocamis_db = getattr(settings, "DATABASES", {}).get("default")


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


class FromAws:

    def __init__(self, month_record: MonthRecord, task_params=None):
        self.month_record = month_record
        self.task_params = task_params

    def revert_stages(self, final_stage: Stage):
        from respond.models import TableFile
        from respond.models import LapSheet
        from respond.models import CrossingSheet
        from django.db import connection
        from task.views import comprobate_brothers

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
        # current_task = self.task_params.get("parent_task")
        # comprobate_brothers(current_task, "finished")

        return [], [], True

    def save_month_analysis(self, **kwargs):
        from django.utils import timezone
        from respond.models import CrossingSheet

        from_aws = kwargs.get("from_aws", False)
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        self.month_record.end_stage("analysis", parent_task)

        related_weeks = self.month_record.weeks.all()
        all_crosses = {}
        all_errors = []
        for related_week in related_weeks:
            crosses = related_week.crosses
            if not crosses:
                error = f"La semana {related_week.iso_week} no tiene cruces"
                all_errors.append(error)
                continue
            for pair, value in crosses["dupli"].items():
                if pair in all_crosses:
                    all_crosses[pair]["dupli"] += value
                else:
                    all_crosses[pair] = {"dupli": value, "shared": 0}
            for pair, value in crosses["shared"].items():
                if pair in all_crosses:
                    all_crosses[pair]["shared"] += value
                else:
                    all_crosses[pair] = {"dupli": 0, "shared": value}
        if all_errors:
            return [], all_errors, False
        CrossingSheet.objects.filter(month_record=self.month_record).delete()

        all_sheet_ids = set()
        current_crosses = []
        for pair, value in all_crosses.items():
            sheet_1, sheet_2 = pair.split("|")
            crossing_sheet = CrossingSheet(
                month_record=self.month_record,
                sheet_file_1_id=sheet_1,
                sheet_file_2_id=sheet_2,
                duplicates_count=value["dupli"],
                shared_count=value["shared"],
                last_crossing=timezone.now(),
            )
            all_sheet_ids.add(sheet_1)
            all_sheet_ids.add(sheet_2)
            current_crosses.append(crossing_sheet)
        self.save_sums(all_sheet_ids)
        CrossingSheet.objects.bulk_create(current_crosses)

        if from_aws:
            self.month_record.last_crossing = timezone.now()
        self.month_record.save()
        return [], [], True

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

    def send_analysis(self):
        # import time
        from respond.models import TableFile
        from data_param.models import FileControl, NameColumn

        all_tasks = []
        insert_stage = Stage.objects.get(name="insert")
        if self.month_record.stage.order >= insert_stage.order:
            error = f"El mes {self.month_record.year_month} ya se insertó"
            return all_tasks, [error], True
        all_table_files = TableFile.objects\
            .filter(
                week_record__month_record=self.month_record,
                collection__isnull=True,
            ).exclude(lap_sheet__sheet_file__behavior_id="invalid")

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
                .order_by("final_field__is_common", "final_field__name")\
                .first()
            if not medicine_field:
                return all_tasks, ["No se encontró campo de medicamento"], True
            unique_medicines.add(medicine_field.final_field_id)
        if len(unique_medicines) > 1:
            return all_tasks, ["Más de un campo de medicamento"], True
        elif len(unique_medicines) == 1:
            medicine_key = unique_medicines.pop()

        for week in self.month_record.weeks.all():
            # if week.last_crossing and week.last_transformation:
            #     if week.last_transformation < week.last_crossing:
            #         continue
            # init_data = WeekRecordSimpleSerializer(week).data
            # table_files = TableFile.objects.filter(
            #     week_record=week,
            #     collection__isnull=True)
            table_files = all_table_files.filter(week_record=week)
            file_names = table_files.values_list("file", flat=True)
            params = {
                "provider_id": week.provider_id,
                "table_files": list(file_names),
                "has_medicine_key": bool(medicine_key),
            }
            self.task_params["models"] = [week, self.month_record]
            self.task_params["function_after"] = "analyze_uniques_after"
            params_after = self.task_params.get("params_after", {})
            # params_after["pet_file_ctrl_id"] = pet_file_ctrl.id
            self.task_params["params_after"] = params_after
            async_task = async_in_lambda(
                "analyze_uniques", params, self.task_params)
            all_tasks.append(async_task)
            # if self.month_record.provider.split_by_delegation:
            #     time.sleep(0.2)
        return all_tasks, [], True

    def merge_files_by_week(self):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile
        from respond.models import DataFile
        from django.utils import timezone
        from django.db.models import F

        related_sheet_files = self.month_record.sheet_files.all()

        my_insert = InsertMonth(self.month_record, self.task_params)
        new_tasks = []
        week_records = self.month_record.weeks.all().prefetch_related(
            "table_files", "table_files__collection", "table_files__lap_sheet",
            "table_files__lap_sheet__sheet_file")

        all_table_files = TableFile.objects \
            .filter(
                week_record__month_record=self.month_record,
                lap_sheet__lap=0,
            ).exclude(lap_sheet__sheet_file__behavior_id="invalid") \
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
            table_task = my_insert.merge_week_base_tables(
                wr, week_base_table_files)
            new_tasks.append(table_task)

        return new_tasks, [], True

    def pre_insert_month(self):
        from task.views import comprobate_status, build_task_params
        from django.db import connection
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile
        from respond.models import LapSheet
        from respond.models import DataFile

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
            .exclude(sheet_file__behavior_id="invalid")

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

        self.task_params["keep_tasks"] = True
        task_params = self.task_params

        class RequestClass:
            def __init__(self):
                self.user = task_params["parent_task"].user
        req = RequestClass()

        task_cats, task_params_cat = build_task_params(
            self.month_record, 'save_month_cat_tables', req,
            **self.task_params)
        new_tasks = []
        errors = []
        cat_tasks = []

        new_tasks.append(task_cats)
        my_insert_cat = InsertMonth(self.month_record, task_params_cat)
        for lap_sheet in pending_lap_sheets:
            current_table_files = collection_table_files.filter(
                lap_sheet=lap_sheet,
                collection__app_label="med_cat",
                inserted=False)
            if not current_table_files.exists():
                continue
            new_task = my_insert_cat.send_lap_tables_to_db(
                lap_sheet, current_table_files, "cat_inserted")
            cat_tasks.append(new_task)
            new_tasks.append(new_task)
        if not cat_tasks:
            comprobate_status(task_cats)

        missing_table_files = TableFile.objects.filter(
            lap_sheet__in=related_lap_sheets,
            collection__app_label="formula",
            inserted=False)
        # base_table_files = TableFile.objects.filter(
        #     lap_sheet__isnull=True,
        #     year_month=self.month_record.year_month,
        #     collection__app_label="formula",
        #     inserted=False)

        task_base, task_params_base = build_task_params(
            self.month_record, 'save_month_base_tables', req,
            **self.task_params)
        new_tasks.append(task_base)
        my_insert_base = InsertMonth(self.month_record, task_params_base)
        base_tasks = []
        for week in self.month_record.weeks.all():
            week_base_table_files = week.table_files.filter(
                lap_sheet__isnull=True,
                collection__app_label="formula",
                inserted=False)
            if not week_base_table_files.exists():
                continue
            week_task = my_insert_base.send_base_tables_to_db(
                week, week_base_table_files)
            base_tasks.append(week_task)
            new_tasks.append(week_task)
        if not base_tasks:
            comprobate_status(task_base)

        for lap_sheet in related_lap_sheets:
            lap_missing_tables = missing_table_files.filter(
                lap_sheet=lap_sheet)
            if not lap_missing_tables:
                lap_sheet.missing_inserted = True
                # lap_sheet.sheet_file.save_stage('insert', [])
            else:
                new_task = my_insert_base.send_lap_tables_to_db(
                    lap_sheet, lap_missing_tables, "missing_inserted")
                new_tasks.append(new_task)

        return new_tasks, errors, True

    def validate_month(self):
        from respond.models import TableFile
        clean_queries = []
        errors = []

        for table_name in ["rx", "drug"]:
            temp_table = f"fm_{self.month_record.temp_table}_{table_name}"
            exists_temp_tables = exist_temp_table(temp_table, "tmp")
            if not exists_temp_tables:
                errors.append(f"No existe la tabla esencial {temp_table}")
        if errors:
            return [], errors, False

        if self.month_record.error_process:
            error_process_list = self.month_record.error_process
            error_process_str = "\n".join(error_process_list)
            blocked_error = "blocked by process " in error_process_str
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
            elif not blocked_error:
                error = f"Existen otros errores: {error_process_str}"
                self.month_record.error_process = [error]
                self.month_record.status_id = "with_errors"
                self.month_record.save()
                return [], [error], True

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
            error = "No se encontraron semanas con medicamentos"
            self.month_record.error_process = [error]
            self.month_record.status_id = "with_errors"
            self.month_record.save()
            return [], [error], True
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

        all_tasks = []
        self.task_params["models"] = [self.month_record]
        async_task = async_in_lambda(
            "validate_temp_tables", params, self.task_params)
        if async_task:
            all_tasks.append(async_task)
        return all_tasks, errors, True

    def indexing_month(self):
        from formula.views import modify_constraints
        errors = []

        for table_name in ["rx", "drug"]:
            temp_table = f"fm_{self.month_record.temp_table}_{table_name}"
            exists_temp_tables = exist_temp_table(temp_table, "tmp")
            if not exists_temp_tables:
                errors.append(f"No existe la tabla esencial {temp_table}")
        if errors:
            return [], errors, False

        if self.month_record.error_process:
            error_process_list = self.month_record.error_process
            error_process_str = "\n".join(error_process_list)
            error = f"Existen otros errores: {error_process_str}"
            self.month_record.error_process = [error]
            self.month_record.status_id = "with_errors"
            self.month_record.save()
            return [], [error], True

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

        all_tasks = []
        self.task_params["models"] = [self.month_record]
        async_task = async_in_lambda(
            "indexing_temp_tables", params, self.task_params)
        if async_task:
            all_tasks.append(async_task)
        return all_tasks, errors, True

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
            errors.append(f"El proveedor no está asociado a ningún cluster")
            return [], errors, False
        formula_tables = ["rx", "drug", "missingrow", "missingfield",
                          "complementrx", "complementdrug", "diagnosisrx"]
        for table_name in formula_tables:
            temp_table = f"fm_{self.month_record.temp_table}_{table_name}"
            exists_temp_tables = exist_temp_table(temp_table, "tmp")
            base_table_name = f"frm_{base_table}_{table_name}"
            exists_base_table = exist_temp_table(base_table_name, "base")
            if not exists_temp_tables:
                if table_name in ["rx", "drug"]:
                    errors.append(f"No existe la tabla esencial {temp_table}")
                else:
                    continue
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

        if errors:
            return [], errors, False

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
        all_tasks = []
        self.task_params["models"] = [self.month_record]
        async_task = async_in_lambda(
            "insert_temp_tables", params, self.task_params)
        if async_task:
            all_tasks.append(async_task)
        return all_tasks, [], True

    def all_base_tables_merged(self, **kwargs):
        from django.utils import timezone
        self.month_record.last_merge = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        self.month_record.end_stage("merge", parent_task)
        self.month_record.save()
        return [], [], True

    def insert_temp_tables_after(self, **kwargs):
        return [], [], True

    def validate_temp_tables_after(self, **kwargs):
        errors = kwargs.get("errors", [])
        return [], [], True

    def indexing_temp_tables_after(self, **kwargs):
        return [], [], True

    def all_base_tables_saved(self, **kwargs):
        from django.utils import timezone
        self.month_record.last_pre_insertion = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        errors = self.month_record.end_stage("pre_insert", parent_task)
        # if not errors:
        #     self.month_record.end_stage("insert", parent_task)
        self.month_record.save()
        return [], [], True

    def all_base_tables_validated(self, **kwargs):
        from django.utils import timezone
        import json
        self.month_record.last_validate = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        errors = self.month_record.end_stage("validate", parent_task)
        for error in errors:
            if "semanas no insertadas en la base" in error:
                week_ids = error.split(": ")[1]
                week_ids = json.loads(week_ids)
                for week_id in week_ids:
                    week = self.month_record.weeks.get(id=week_id)
                    week.last_pre_insertion = None
                    week.table_files.update(inserted=False)
                    week.save()
                self.month_record.stage_id = "pre_insert"
                self.month_record.status_id = "with_errors"
                self.month_record.save()
                return [], errors, False
        # if not errors:
        #     self.month_record.end_stage("insert", parent_task)
        self.month_record.save()
        return [], [], True

    def all_base_tables_indexed(self, **kwargs):
        # self.month_record.last_indexing = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        self.month_record.end_stage("indexing", parent_task)
        # if not errors:
        #     self.month_record.end_stage("insert", parent_task)
        self.month_record.save()
        return [], [], True

    def all_temp_tables_inserted(self, **kwargs):
        from django.utils import timezone
        # self.month_record.last_insertion = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        errors = self.month_record.end_stage("insert", parent_task)
        # if not errors:
        #     self.month_record.end_stage("insert", parent_task)
        self.month_record.save()
        return [], [], True
