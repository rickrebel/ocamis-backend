from classify_task.models import Stage
from inai.models import EntityMonth
from task.serverless import async_in_lambda


class FromAws:

    def __init__(self, entity_month: EntityMonth, task_params=None):
        self.entity_month = entity_month
        self.task_params = task_params

    def revert_stages(self):
        from inai.models import TableFile, CrossingSheet
        self.entity_month.stage_id = "init_month"
        self.entity_month.status_id = "finished"
        self.entity_month.last_crossing = None
        self.entity_month.last_merge = None
        self.entity_month.last_pre_insertion = None
        self.entity_month.save()
        base_table_files = TableFile.objects.filter(
            entity_week__entity_month=self.entity_month,
            collection__isnull=False)
        base_table_files.delete()
        lap_table_files = TableFile.objects.filter(
            entity_week__entity_month=self.entity_month,
            lap_sheet__isnull=False)
        lap_table_files.update(
            inserted=False,
            rx_count=0,
            duplicates_count=0,
            shared_count=0,
        )
        CrossingSheet.objects.filter(
            entity_month=self.entity_month).delete()
        entity_weeks = self.entity_month.weeks.all()
        entity_weeks.update(
            rx_count=0,
            drugs_count=0,
            duplicates_count=0,
            shared_count=0,
            last_crossing=None,
            last_merge=None,
            last_pre_insertion=None,
            crosses=None,
        )
        return [], [], True

    def save_month_analysis(self, **kwargs):
        from django.db.models import Sum
        from django.utils import timezone
        from inai.models import CrossingSheet, SheetFile, LapSheet

        from_aws = kwargs.get("from_aws", False)
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        self.entity_month.end_stage("analysis", parent_task)

        related_weeks = self.entity_month.weeks.all()
        all_crosses = {}
        for related_week in related_weeks:
            crosses = related_week.crosses
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
        CrossingSheet.objects.filter(entity_month=self.entity_month).delete()

        all_sheet_ids = set()
        current_crosses = []
        for pair, value in all_crosses.items():
            sheet_1, sheet_2 = pair.split("|")
            crossing_sheet = CrossingSheet(
                entity_month=self.entity_month,
                sheet_file_1_id=sheet_1,
                sheet_file_2_id=sheet_2,
                duplicates_count=value["dupli"],
                shared_count=value["shared"],
                last_crossing=timezone.now(),
            )
            all_sheet_ids.add(sheet_1)
            all_sheet_ids.add(sheet_2)
            current_crosses.append(crossing_sheet)

        CrossingSheet.objects.bulk_create(current_crosses)

        sum_fields = [
            "drugs_count", "rx_count", "duplicates_count", "shared_count"]
        query_sheet_sums = [Sum(field) for field in sum_fields]
        # query_annotations = {field: Sum(field) for field in sum_fields}
        all_laps = LapSheet.objects.filter(
            sheet_file__in=all_sheet_ids, lap=0)
        for lap_sheet in all_laps:
            table_sums = lap_sheet.table_files.aggregate(*query_sheet_sums)
            for field in sum_fields:
                setattr(lap_sheet.sheet_file, field, table_sums[field + "__sum"])
            lap_sheet.sheet_file.save()

        query_sums = [Sum(field) for field in sum_fields]
        result_sums = self.entity_month.weeks.all().aggregate(*query_sums)
        # print("result_sums", result_sums)
        for field in sum_fields:
            setattr(self.entity_month, field, result_sums[field + "__sum"])
        if from_aws:
            self.entity_month.last_crossing = timezone.now()
        self.entity_month.save()
        return [], [], True

    def send_analysis(self):
        # import time
        from scripts.common import build_s3
        from inai.models import TableFile

        all_tasks = []
        insert_stage = Stage.objects.get(name="insert")
        if self.entity_month.stage.order >= insert_stage.order:
            error = f"El mes {self.entity_month.year_month} ya se insertó"
            return all_tasks, [error], True
        all_table_files = TableFile.objects\
            .filter(
                entity_week__entity_month=self.entity_month,
                collection__isnull=True,
            ).exclude(lap_sheet__sheet_file__behavior_id="invalid")

        for week in self.entity_month.weeks.all():
            if week.last_crossing:
                if week.last_transformation < week.last_crossing:
                    continue
            # init_data = EntityWeekSimpleSerializer(week).data
            # table_files = TableFile.objects.filter(
            #     entity_week=week,
            #     collection__isnull=True)
            table_files = all_table_files.filter(entity_week=week)
            file_names = table_files.values_list("file", flat=True)
            params = {
                "init_data": {
                    "entity_id": week.entity_id,
                    "table_files": list(file_names)
                },
                "s3": build_s3(),
            }
            self.task_params["models"] = [week]
            self.task_params["function_after"] = "analyze_uniques_after"
            params_after = self.task_params.get("params_after", {})
            # params_after["pet_file_ctrl_id"] = pet_file_ctrl.id
            self.task_params["params_after"] = params_after
            async_task = async_in_lambda(
                "analyze_uniques", params, self.task_params)
            all_tasks.append(async_task)
            # if self.entity_month.entity.split_by_delegation:
            #     time.sleep(0.2)
        return all_tasks, [], True

    def merge_files_by_week(self):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import DataFile
        from django.utils import timezone

        related_sheet_files = self.entity_month.sheet_files.all()
        data_files_ids = related_sheet_files.values_list(
            "data_file_id", flat=True).distinct()
        data_files = DataFile.objects.filter(id__in=data_files_ids)
        data_files.update(stage_id='merge', status_id='pending')

        my_insert = InsertMonth(self.entity_month, self.task_params)
        new_tasks = []
        entity_weeks = self.entity_month.weeks.all()

        for ew in entity_weeks:
            if ew.last_merge:
                if ew.last_transformation < ew.last_crossing < ew.last_merge:
                    continue
            if self.entity_month.entity_id == 55 and ew.complete:
                continue
            week_base_table_files = ew.table_files.filter(
                lap_sheet__lap=0).prefetch_related("lap_sheet__sheet_file")
            if week_base_table_files.count() == 0:
                ew.last_transformation = timezone.now()
                ew.save()
                continue
            table_task = my_insert.merge_week_base_tables(
                ew, week_base_table_files)
            new_tasks.append(table_task)

        return new_tasks, [], True

    def pre_insert_month(self):
        from task.views import build_task_params
        from django.db import connection
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import LapSheet, TableFile, DataFile

        # CREATE TABLE fm_55_201902_rx (LIKE formula_rx INCLUDING CONSTRAINTS);
        # CREATE TABLE fm_55_201902_drug (LIKE formula_drug INCLUDING CONSTRAINTS);
        queries = {"create": [], "drop": []}
        for table_name in ["rx", "drug", "missingrow", "missingfield"]:
            temp_table = f"fm_{self.entity_month.temp_table}_{table_name}"
            queries["drop"].append(f"""
                DROP TABLE IF EXISTS {temp_table} CASCADE; 
            """)
            queries["create"].append(f"""
                CREATE TABLE {temp_table}
                (LIKE formula_{table_name} INCLUDING CONSTRAINTS);
            """)
        cursor = connection.cursor()
        for operation in ["drop", "create"]:
            for query in queries[operation]:
                cursor.execute(query)
        cursor.close()

        # INSERT INTO formula_rx
        # SELECT *
        # FROM fm_55_201902_rx;
        # INSERT INTO formula_drug
        # SELECT *
        # FROM fm_55_201902_drug;

        # DROP TABLE fm_55_201902_rx;
        # DROP TABLE fm_55_201902_drug;

        month_table_files = TableFile.objects\
            .filter(
                entity_week__entity_month=self.entity_month,
                collection__isnull=True
            )\
            .exclude(inserted=True)
        related_sheet_files = self.entity_month.sheet_files.all()

        related_lap_sheets = LapSheet.objects\
            .filter(sheet_file__in=related_sheet_files)\
            .exclude(sheet_file__behavior_id="invalid")
        data_files_ids = related_sheet_files.values_list(
            "data_file_id", flat=True).distinct()
        data_files = DataFile.objects.filter(id__in=data_files_ids)
        data_files.update(stage_id='insert', status_id='pending')

        pending_lap_sheets = related_lap_sheets.filter(
            cat_inserted=False, lap=0)

        collection_table_files = TableFile.objects.filter(
            lap_sheet__in=pending_lap_sheets,
            collection__app_label="med_cat",
            inserted=False)
        errors = []
        if not collection_table_files.exists() and not month_table_files.exists():
            error = ["No existen tablas por insertar para el mes "
                     f"{self.entity_month.year_month}"]
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
            self.entity_month, 'save_month_cat_tables', req,
            **self.task_params)
        new_tasks = []
        errors = []
        new_tasks.append(task_cats)
        my_insert_cat = InsertMonth(self.entity_month, task_params_cat)
        for lap_sheet in pending_lap_sheets:
            current_table_files = collection_table_files.filter(
                lap_sheet=lap_sheet,
                collection__app_label="med_cat",
                inserted=False)
            if not current_table_files.exists():
                continue
            new_task = my_insert_cat.send_lap_tables_to_db(
                lap_sheet, current_table_files, "cat_inserted")
            new_tasks.append(new_task)

        missing_table_files = TableFile.objects.filter(
            lap_sheet__in=related_lap_sheets,
            collection__app_label="formula",
            inserted=False)
        # base_table_files = TableFile.objects.filter(
        #     lap_sheet__isnull=True,
        #     year_month=self.entity_month.year_month,
        #     collection__app_label="formula",
        #     inserted=False)

        task_base, task_params_base = build_task_params(
            self.entity_month, 'save_month_base_tables', req,
            **self.task_params)
        new_tasks.append(task_base)
        my_insert_base = InsertMonth(self.entity_month, task_params_base)
        for week in self.entity_month.weeks.all():
            week_base_table_files = week.table_files.filter(
                lap_sheet__isnull=True,
                collection__app_label="formula",
                inserted=False)
            if not week_base_table_files.exists():
                continue
            week_task = my_insert_base.send_base_tables_to_db(
                week, week_base_table_files)
            new_tasks.append(week_task)

        for lap_sheet in related_lap_sheets:
            lap_missing_tables = missing_table_files.filter(
                lap_sheet=lap_sheet)
            if not lap_missing_tables:
                lap_sheet.missing_inserted = True
                lap_sheet.sheet_file.save_stage('insert', [])
            else:
                new_task = my_insert_base.send_lap_tables_to_db(
                    lap_sheet, lap_missing_tables, "missing_inserted")
                new_tasks.append(new_task)

        return new_tasks, errors, True

    def all_base_tables_merged(self, **kwargs):
        from django.utils import timezone
        self.entity_month.last_merge = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        self.entity_month.end_stage("merge", parent_task)
        self.entity_month.save()
        return [], [], True

    def all_base_tables_saved(self, **kwargs):
        from django.utils import timezone
        self.entity_month.last_pre_insertion = timezone.now()
        current_task = self.task_params.get("parent_task")
        parent_task = current_task.parent_task
        errors = self.entity_month.end_stage("pre_insert", parent_task)
        # if not errors:
        #     self.entity_month.end_stage("insert", parent_task)
        self.entity_month.save()
        return [], [], True
