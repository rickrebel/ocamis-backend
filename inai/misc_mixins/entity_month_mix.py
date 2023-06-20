from inai.models import EntityMonth
from task.serverless import async_in_lambda


class FromAws:

    def __init__(self, entity_month: EntityMonth, task_params=None):
        self.entity_month = entity_month
        self.task_params = task_params

    def save_month_analysis(self, **kwargs):
        from django.db.models import Sum
        from django.utils import timezone
        sum_fields = [
            "drugs_count", "rx_count", "duplicates_count", "shared_count"]

        query_sums = [Sum(field) for field in sum_fields]
        result_sums = self.entity_month.weeks.all().aggregate(*query_sums)
        print("result_sums", result_sums)
        for field in sum_fields:
            setattr(self.entity_month, field, result_sums[field + "__sum"])
        self.entity_month.last_crossing = timezone.now()
        self.entity_month.save()

        return [], [], True

    def send_analysis(self, related_weeks: list):
        from scripts.common import build_s3
        from inai.models import TableFile
        from inai.api.serializers import (
            EntityWeekSimpleSerializer, TableFileAwsSerializer)

        all_tasks = []
        for week in related_weeks:
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
            self.task_params["models"] = [week]
            self.task_params["function_after"] = "analyze_uniques_after"
            params_after = self.task_params.get("params_after", { })
            # params_after["pet_file_ctrl_id"] = pet_file_ctrl.id
            self.task_params["params_after"] = params_after
            async_task = async_in_lambda(
                "analyze_uniques", params, self.task_params)
            all_tasks.append(async_task)
        return all_tasks, [], True

    def insert_month(self):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import LapSheet, TableFile, SheetFile
        # print("HOLA INSERT_MONTH")

        # month_table_files = self.entity_month.weeks.table_files.all()
        month_table_files = TableFile.objects.filter(
            entity_week__entity_month=self.entity_month)
        all_entity_table_files = TableFile.objects.filter(
            entity_week__entity=self.entity_month.entity)
        related_weeks = self.entity_month.weeks.all()\
            .values_list("year_week", flat=True)
        all_month_table_files = all_entity_table_files.filter(
            year_week__in=related_weeks)
        all_year_months = all_month_table_files.values_list(
            "year_month", flat=True).distinct()

        # related_lap_sheets = LapSheet.objects.filter(
        #     table_files__year_month__in=all_year_months)
        related_sheet_files = self.entity_month.sheet_files.all()
        related_lap_sheets = LapSheet.objects.filter(
            sheet_file__in=related_sheet_files)
        # .filter(sheet_file__data_file__in=month_table_files)\
        lap_sheets = LapSheet.objects\
            .filter(table_files__in=month_table_files)\
            .exclude(sheet_file__behavior_id="invalid")
        collection_table_files = TableFile.objects.filter(
            lap_sheet__in=related_lap_sheets,
            collection__app_label="med_cat", inserted=False)
        month_table_files = month_table_files.exclude(inserted=True)
        if not collection_table_files.exists() and not month_table_files.exists():
            errors = ["No existen tablas por insertar para el mes "
                      f"{self.entity_month.year_month}"]
            print("errors", errors)
            return [], errors, False
        month_sheet_files = SheetFile.objects.filter(
            id__in=lap_sheets.values_list("sheet_file_id", flat=True))\
            .distinct()
        if month_sheet_files.filter(behavior_id="pending").exists():
            errors = [f"Hay pestañas pendientes de clasificar para el mes "
                      f"{self.entity_month.year_month}"]
            print("errors", errors)
            return [], errors, False
        # lap_sheets = lap_sheets.filter(inserted=False)
        my_insert = InsertMonth(self.entity_month, self.task_params)
        new_tasks = []
        weeks = month_table_files.values_list(
            "entity_week_id", flat=True).distinct()
        entity_weeks = self.entity_month.weeks.filter(id__in=weeks)

        # ENVÍO DE TABLAS DE COLECCIÓN
        for lap_sheet in related_lap_sheets:
            current_table_files = collection_table_files.filter(
                lap_sheet=lap_sheet, collection__app_label="med_cat")
            new_task = my_insert.send_lap_tables_to_db(
                lap_sheet, current_table_files, "cat_inserted")
            new_tasks.append(new_task)
        print("entity_weeks", entity_weeks)
        for entity_week in entity_weeks:
            # week_base_table_files = all_entity_table_files.filter(
            #     iso_year=entity_week.iso_year,
            #     iso_week=entity_week.iso_week,
            #     lap_sheet__lap=0)
            week_base_table_files = entity_week.table_files.filter(
                lap_sheet__lap=0)
            table_task = my_insert.merge_week_base_tables(
                entity_week, week_base_table_files)
            new_tasks.append(table_task)
        if not new_tasks:
            return self.save_formula_tables(self.task_params)

        return new_tasks, [], True

    def save_formula_tables(self, task_params, **kwargs):
        from inai.misc_mixins.insert_month_mix import InsertMonth
        from inai.models import LapSheet, TableFile
        errors = []
        new_tasks = []
        month_table_files = self.entity_month.weeks.table_files.all()
        lap_sheets = LapSheet.objects\
            .filter(sheet_file__data_file__in=month_table_files)\
            .exclude(sheet_file__behavior_id="invalid")
        missing_table_files = TableFile.objects.filter(
            lap_sheet__in=lap_sheets,
            collection__app_label="formula",
            inserted=False)
        base_table_files = TableFile.objects.filter(
            lap_sheet__isnull=True,
            year_month=self.entity_month.year_month,
            collection__app_label="formula",
            inserted=False)
        if not missing_table_files.exists() and not base_table_files.exists():
            return new_tasks, errors, True
        my_insert = InsertMonth(self.entity_month, task_params)
        base_task = my_insert.send_base_tables_to_db(
            self.entity_month, base_table_files)
        new_tasks.append(base_task)
        for lap_sheet in lap_sheets:
            lap_missing_tables = missing_table_files.filter(lap_sheet=lap_sheet)
            new_task = my_insert.send_lap_tables_to_db(
                lap_sheet, lap_missing_tables, "inserted")
            new_tasks.append(new_task)

        return new_tasks, errors, True
