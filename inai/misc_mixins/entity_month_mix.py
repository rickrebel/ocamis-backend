from inai.models import EntityMonth
from task.serverless import async_in_lambda


class FromAws:

    def __init__(self, entity_month: EntityMonth, task_params=None):
        self.entity_month = entity_month
        self.task_params = task_params

    def save_month_analysis(self, **kwargs):
        from django.db.models import Sum
        from django.utils import timezone
        from inai.models import CrossingSheet, SheetFile, LapSheet

        from_aws = kwargs.get("from_aws", False)

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

        # space
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
        from inai.api.serializers import (
            EntityWeekSimpleSerializer, TableFileAwsSerializer)

        all_tasks = []
        for week in self.entity_month.weeks.all():
            if week.last_crossing:
                if week.last_transformation < week.last_crossing:
                    continue
            init_data = EntityWeekSimpleSerializer(week).data
            table_files = TableFile.objects.filter(
                entity_week=week,
                collection__isnull=True)
            init_data["table_files"] = TableFileAwsSerializer(
                table_files, many=True).data
            params = {
                "init_data": init_data,
                "s3": build_s3(),
            }
            self.task_params["models"] = [week, self.entity_month]
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

    def save_month_analysis_prev(self, **kwargs):
        from django.db.models import Sum
        from django.utils import timezone
        from inai.models import CrossingSheet, SheetFile, LapSheet

        crossing_sheets = CrossingSheet.objects.filter(
            entity_week__entity_month=self.entity_month).distinct()
        crossings_simple = crossing_sheets.values_list(
            "sheet_file_1", "sheet_file_2").distinct()
        # crossing_sums = crossing_sheets\
        #     .aggregate(Sum("duplicates_count"), Sum("shared_count"))\
        #     .values_list(
        #         "sheet_file_1", "sheet_file_2", "duplicates_count__sum",
        #         "shared_count__sum")
        # print("crossing_sums", crossing_sums)
        all_sheet_ids = set()
        for crossing in crossings_simple:
            current_crossings = crossing_sheets.filter(
                entity_month__isnull=True,
                sheet_file_1_id=crossing[0],
                sheet_file_2_id=crossing[1])
            crossing_sums = current_crossings.aggregate(
                Sum("duplicates_count"), Sum("shared_count"))
            crossing_sheet, _ = CrossingSheet.objects.get_or_create(
                entity_month=self.entity_month,
                sheet_file_1_id=crossing[0],
                sheet_file_2_id=crossing[1])
            all_sheet_ids.add(crossing[0])
            all_sheet_ids.add(crossing[1])
            crossing_sheet.duplicates_count = crossing_sums["duplicates_count__sum"]
            crossing_sheet.shared_count = crossing_sums["shared_count__sum"]
            crossing_sheet.last_crossing = timezone.now()
            crossing_sheet.save()

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

        # space
        query_sums = [Sum(field) for field in sum_fields]
        result_sums = self.entity_month.weeks.all().aggregate(*query_sums)
        # print("result_sums", result_sums)
        for field in sum_fields:
            setattr(self.entity_month, field, result_sums[field + "__sum"])
        self.entity_month.last_crossing = timezone.now()
        self.entity_month.save()
        return [], [], True

    def rebuild_month(self):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import DataFile

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
            table_task = my_insert.merge_week_base_tables(
                ew, week_base_table_files)
            new_tasks.append(table_task)

        return new_tasks, [], True

    def insert_month(self):
        from task.views import build_task_params
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import LapSheet, TableFile, DataFile
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
        if related_sheet_files.filter(behavior_id="pending").exists():
            error = [f"Hay pestañas pendientes de clasificar para el mes "
                      f"{self.entity_month.year_month}"]
            errors.append(error)
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
                lap_sheet=lap_sheet, collection__app_label="med_cat")
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
            week_task = my_insert_base.send_base_tables_to_db(
                week, week_base_table_files)
            new_tasks.append(week_task)

        for lap_sheet in related_lap_sheets:
            lap_missing_tables = missing_table_files.filter(lap_sheet=lap_sheet)
            if not lap_missing_tables:
                lap_sheet.missing_inserted = True
                lap_sheet.sheet_file.save_stage('insert', [])
            else:
                new_task = my_insert_base.send_lap_tables_to_db(
                    lap_sheet, lap_missing_tables, "missing_inserted")
                new_tasks.append(new_task)

        return new_tasks, errors, True

    def save_formula_tables(self, task_params, **kwargs):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import LapSheet, TableFile
        from task.views import build_task_params
        errors = []
        new_tasks = []
        # month_table_files = []
        # for week in self.entity_month.weeks.all():
        #     month_table_files.extend(week.table_files.all().values_list(
        #         "id", flat=True))

        class RequestClass:
            def __init__(self):
                self.user = task_params["parent_task"].user
        req = RequestClass()
        task_kwargs = {
            "parent_task": task_params["parent_task"],
            # "finished_function": "all_base_tables_saved"
        }
        # base_task = my_insert.send_base_tables_to_db(
        #     self.entity_month, base_table_files)
        # new_tasks.append(base_task)
        # space
        return new_tasks, errors, True

    def all_base_tables_merged(self, **kwargs):
        from django.utils import timezone
        self.entity_month.last_merge = timezone.now()
        self.entity_month.save()
        return [], [], True

    def all_base_tables_saved(self, **kwargs):
        from django.utils import timezone
        self.entity_month.last_insertion = timezone.now()
        self.entity_month.save()
        return [], [], True

