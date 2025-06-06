from classify_task.models import Stage
from inai.models import MonthRecord
# from task.serverless import async_in_lambda
from task.builder import TaskBuilder
from task.main_views_aws import AwsFunction
from django.conf import settings
ocamis_db = getattr(settings, "DATABASES", {}).get("default")

formula_tables = [
    "rx", "drug", "missingrow", "missingfield", "diagnosisrx",
    "complementrx", "complementdrug"]


class MonthRecordMix:

    def __init__(self, month_record: MonthRecord, base_task: AwsFunction = None):
        self.month_record = month_record
        self.base_task = base_task
        self.params = {
            "month_record_id": self.month_record.id,
            "temp_table": self.month_record.temp_table,
            "db_config": ocamis_db,
        }

    def revert_stages(self, final_stage: Stage, is_self_revert=False):
        from respond.models import TableFile
        from respond.models import LapSheet
        from respond.models import CrossingSheet
        from django.db import connection

        self.month_record.stage = final_stage
        if is_self_revert:
            previous_stage = Stage.objects\
                .filter(next_stage=final_stage)\
                .order_by("order")\
                .first()
            if previous_stage:
                self.month_record.stage = previous_stage
            self.month_record.status_id = "finished"
        elif final_stage.name == "revert_stages":
            self.month_record.status_id = "finished"
        else:
            self.month_record.status_id = "created"

        self.month_record.error_process = None
        week_records = self.month_record.weeks.all()
        base_table_files = TableFile.objects.filter(
            week_record__month_record=self.month_record,
            collection__isnull=False)
        sheet_files = self.month_record.sheet_files.all()

        auto_stages = [
            "analysis", "merge", "pre_insert", "validate", "indexing", "insert"]
        month_stages = Stage.objects\
            .filter(order__gte=final_stage.order, stage_group="months")\
            .values("name", "order", "field_last_edit")

        next_stages = []
        for month_stage in month_stages:
            if month_stage["name"] in auto_stages:
                self.month_record.__setattr__(
                    month_stage["field_last_edit"], None)
            next_stages.append(month_stage["name"])

        # stage_pre_insert = Stage.objects.get(name="pre_insert")
        # if final_stage.order <= stage_pre_insert.order:
        if "pre_insert" in next_stages:
            # self.month_record.last_pre_insertion = None
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

            for table_name in formula_tables:
                temp_table = f"tmp.fm_{self.month_record.temp_table}_{table_name}"
                query_drop = f"DROP TABLE IF EXISTS {temp_table} CASCADE;"
                cursor.execute(query_drop)
            cursor.close()
            connection.commit()
            connection.close()

        # stage_merge = Stage.objects.get(name="merge")
        # if final_stage.order <= stage_merge.order:
        if "merge" in next_stages:
            # self.month_record.last_merge = None
            base_table_files.delete()
            week_records.update(last_merge=None)

        # stage_analysis = Stage.objects.get(name="analysis")
        # if final_stage.order <= stage_analysis.order:
        if "analysis" in next_stages:
            # self.month_record.last_crossing = None
            self.month_record.last_behavior = None
            lap_table_files = TableFile.objects.filter(
                week_record__month_record=self.month_record,
                lap_sheet__isnull=False)
            lap_table_files.update(
                rx_count=0,
                self_repeated_count=0,
                duplicates_count=0,
                shared_count=0)
            CrossingSheet.objects.filter(
                month_record=self.month_record).delete()
            week_records.update(
                rx_count=0,
                drugs_count=0,
                duplicates_count=0,
                self_repeated_count=0,
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

        insert_stage = Stage.objects.get(name="insert")
        if self.month_record.stage.order >= insert_stage.order:
            error = f"El mes {self.month_record.year_month} ya se insertó"
            return self.base_task.add_errors([error], http_response=True)
        all_table_files = TableFile.objects\
            .filter(
                week_record__month_record=self.month_record,
                collection__isnull=True,
            ).exclude(lap_sheet__sheet_file__behavior__is_discarded=True)

        sfs = "petition_file_control__data_files__sheet_files"
        months = "__laps__table_files__week_record__month_record"
        filter_fc = {f"{sfs}{months}": self.month_record,
                     f"{sfs}__behavior__is_discarded": False}
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
                table_file = table_files\
                    .filter(file=first_duplicate_file)\
                    .first()
                error = (f"Se están intentando enviar el mismo archivo "
                         f"{table_file.id} "
                         f"llamado {first_duplicate_file} más de una vez")
                return self.base_task.add_errors_and_raise([error])
            params = {
                "provider_id": week.provider_id,
                "table_files": file_names,
                "has_medicine_key": bool(medicine_key),
            }
            week_base_task = TaskBuilder(
                "analyze_uniques", parent_class=self.base_task,
                models=[week, self.month_record], params=params,
                function_after="analyze_uniques_after")
            # print("week_base_task", week_base_task)
            week_base_task.async_in_lambda()

    def merge_files_by_week(self):
        # print("merge_files_by_week")
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile
        from django.utils import timezone
        from django.db.models import F

        # related_sheet_files = self.month_record.sheet_files.all()

        my_insert = InsertMonth(self.month_record, self.base_task)
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

    def pre_insert_month(self):
        from django.db import connection
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from respond.models import TableFile, LapSheet

        # CREATE TABLE fm_55_201902_rx (LIKE formula_rx INCLUDING CONSTRAINTS);
        # CREATE TABLE fm_55_201902_drug (LIKE formula_drug INCLUDING CONSTRAINTS);
        queries = {"create": [], "drop": []}

        drug_table = f"fm_{self.month_record.temp_table}_drug"
        cursor = connection.cursor()
        exists_temp_tables = exist_temp_table(drug_table, "tmp")

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
            .filter(week_record__month_record=self.month_record,
                    collection__isnull=True)\
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
        if errors:
            print("error", errors)

        cats_task = TaskBuilder(
            "save_month_cat_tables", keep_tasks=True,
            parent_class=self.base_task, models=[self.month_record],
            finished_function="save_lap_sheets_inserted")

        my_insert_cat = InsertMonth(self.month_record, base_task=cats_task)

        my_insert_cat.send_cat_tables_to_db()

        missing_table_files = TableFile.objects.filter(
            lap_sheet__in=related_lap_sheets,
            collection__app_label="formula",
            inserted=False)

        formula_task = TaskBuilder(
            "save_month_base_tables", keep_tasks=True,
            models=[self.month_record], parent_class=self.base_task)
        my_insert_base = InsertMonth(self.month_record, base_task=formula_task)
        for week in self.month_record.weeks.all():
            week_base_table_files = week.table_files.filter(
                lap_sheet__isnull=True,
                collection__app_label="formula",
                inserted=False)
            if not week_base_table_files.exists():
                continue
            my_insert_base.send_base_tables_to_db(week, week_base_table_files)

        for lap_sheet in related_lap_sheets:
            lap_missing_tables = missing_table_files.filter(
                lap_sheet=lap_sheet)
            if lap_missing_tables.exists() and not lap_sheet.missing_inserted:
                my_insert_base.send_lap_tables_to_db(
                    lap_sheet, lap_missing_tables)
            else:
                lap_sheet.missing_inserted = True
                lap_sheet.save()
        if not formula_task.new_tasks:
            formula_task.comprobate_status()

        if not cats_task.new_tasks:
            cats_task.comprobate_status()

    def validate_month(self):
        from respond.models import TableFile
        clean_queries = []

        self.check_temp_tables()

        error_process_str = self.get_error_process_str()
        temp_table_base = f"tmp.fm_{self.month_record.temp_table}"
        if error_process_str:
            if "semanas con más medicamentos" in error_process_str:
                models = {
                    "rx": "uuid_folio",
                    "drug": "uuid",
                }
                for table_name, field in models.items():
                    # temp_table = f"tmp.fm_{self.month_record.temp_table}_{table_name}"
                    temp_table = f"{temp_table_base}_{table_name}"
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
        # temp_drug = f"tmp.fm_{self.month_record.temp_table}_drug"
        temp_drug = f"{temp_table_base}_drug"
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

        self.params.update({
            "clean_queries": clean_queries,
            "count_query": count_query,
            "drugs_object": drugs_object,
            "last_query": last_query,
        })

        validate_task = TaskBuilder(
            "validate_temp_tables", params=self.params,
            models=[self.month_record], parent_class=self.base_task)
        validate_task.async_in_lambda()

    def indexing_month(self):
        from formula.views import modify_constraints

        self.check_temp_tables()

        error_process_str = self.get_error_process_str()
        if error_process_str:
            error = f"Existen otros errores: {error_process_str}"
            self.month_record.save_error_process([error])
            self.base_task.add_errors([error], http_response=True)

        constraint_queries = modify_constraints(
            True, False, self.month_record.temp_table)
        self.params["constraint_queries"] = constraint_queries

        self.params["last_query"] = f"""
            UPDATE public.inai_entitymonth
            SET last_indexing = now()
            WHERE id = {self.month_record.id}
        """

        indexing_task = TaskBuilder(
            "indexing_temp_tables", params=self.params,
            parent_class=self.base_task, models=[self.month_record])
        indexing_task.async_in_lambda()

    def final_insert_month(self):
        try:
            base_table = self.month_record.cluster.name
        except Exception as e:
            error = f"El mes no está asociado a ningún cluster:"
            self.base_task.add_errors([error], http_response=True)
            raise e
        self.check_temp_tables()
        for table_name in formula_tables:
            self.build_formula_table_queries(base_table, table_name)

        self.params["first_query"] = f"""
            SELECT last_insertion IS NOT NULL AS last_insertion
            FROM public.inai_entitymonth
            WHERE id = {self.month_record.id}
        """
        self.params["last_query"] = f"""
            UPDATE public.inai_entitymonth
            SET last_insertion = now()
            WHERE id = {self.month_record.id}
        """

        insert_task = TaskBuilder(
            "insert_temp_tables", params=self.params,
            parent_class=self.base_task, models=[self.month_record])
        insert_task.async_in_lambda()

    def build_formula_table_queries(self, base_table, table_name):
        temp_table = f"fm_{self.month_record.temp_table}_{table_name}"

        exists_temp_tables = exist_temp_table(temp_table, "tmp")
        if not exists_temp_tables:
            return

        base_table_name = f"frm_{base_table}_{table_name}"
        exists_base_table = exist_temp_table(base_table_name, "base")
        if not exists_base_table:
            create_base_table = f"""
                CREATE TABLE base.{base_table_name}
                (LIKE public.formula_{table_name} INCLUDING CONSTRAINTS);
            """
            self.add_param_query("create_base_tables", create_base_table)
        insert_query = f"""
            INSERT INTO base.{base_table_name}
            SELECT *
            FROM tmp.{temp_table};
        """
        self.add_param_query("insert_queries", insert_query)

        self.export_month_table_queries(table_name, temp_table)

        drop_query = f"DROP TABLE IF EXISTS tmp.{temp_table} CASCADE;"
        self.add_param_query("drop_queries", drop_query)

    def export_month_table_queries(self, table_name, temp_table):
        from respond.models import (
            final_month_path, MonthTableFile, get_month_file_name)
        from formula.views import copy_export_s3
        from data_param.models import Collection

        file_name = get_month_file_name(
            table_name=table_name, month_record=self.month_record)
        month_path = final_month_path(self.month_record, file_name)
        self.add_param_query("month_paths", month_path)
        export_table_s3 = copy_export_s3(f"tmp.{temp_table}", month_path)
        self.add_param_query("export_tables_s3", export_table_s3)
        collection = Collection.objects.get(
            app_label="formula", model_name__iexact=table_name)
        MonthTableFile.objects.get_or_create(
            month_record=self.month_record, table_name=temp_table,
            collection=collection, file=file_name)

    def add_param_query(self, key, query):
        self.params.setdefault(key, [])
        self.params[key].append(query)

    def save_sums(self, all_sheet_ids):
        from respond.models import LapSheet, SheetFile
        from django.db.models import Sum

        sum_fields = [
            "drugs_count", "rx_count",
            "duplicates_count", "shared_count", "self_repeated_count"]
        query_sheet_sums = [Sum(field) for field in sum_fields]
        # query_annotations = {field: Sum(field) for field in sum_fields}
        print("all_sheet_ids", all_sheet_ids)
        # all_laps = LapSheet.objects\
        #     .filter(sheet_file_id__in=all_sheet_ids, lap=0)\
        #     .select_related("sheet_file")\
        #     .prefetch_related("table_files")
        init_sheets = SheetFile.objects\
            .filter(id__in=all_sheet_ids)
        month_sheets = self.month_record.sheet_files.exclude(
            id__in=all_sheet_ids)
        all_sheets = init_sheets | month_sheets
        all_laps = LapSheet.objects\
            .filter(sheet_file__in=all_sheets, lap=0)\
            .select_related("sheet_file")\
            .prefetch_related("table_files")
        # print("all_laps", all_laps)
        for lap_sheet in all_laps:
            table_sums = lap_sheet.table_files.aggregate(*query_sheet_sums)
            for field in sum_fields:
                setattr(lap_sheet.sheet_file, field,
                        table_sums[f"{field}__sum"] or 0)
            lap_sheet.sheet_file.save()
        # for sheet in all_sheets:
        #     table_sums = sheet.table_files.aggregate(*query_sheet_sums)
        #     for field in sum_fields:
        #         setattr(sheet, field, table_sums[f"{field}__sum"] or 0)
        #     sheet.save()

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
