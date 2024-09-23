from inai.misc_mixins.month_record_mix import MonthRecordMix


class FromAws(MonthRecordMix):

    def revert_stages_after(self, **kwargs):
        pass

    def save_month_analysis(self, **kwargs):
        from django.utils import timezone
        from respond.models import CrossingSheet

        self.month_record.end_stage("analysis", self.base_task.main_task)

        related_weeks = self.month_record.weeks.all()
        all_crosses = {}
        all_errors = []
        all_warnings = []
        for related_week in related_weeks:
            crosses = related_week.crosses
            if not crosses:
                warning = f"La semana {related_week.iso_week} no tiene cruces"
                all_warnings.append(warning)
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
        print("all_errors in save_month_analysis: ", all_errors)
        print("all_warnings in save_month_analysis: ", all_warnings)
        if all_errors:
            self.base_task.add_errors_and_raise(all_errors)
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

        if self.base_task.from_aws:
            self.month_record.last_crossing = timezone.now()
        self.month_record.save()

    def all_base_tables_merged(self, **kwargs):
        from django.utils import timezone
        self.month_record.last_merge = timezone.now()
        self.month_record.end_stage("merge", self.base_task.main_task)
        self.month_record.save()

    def insert_temp_tables_after(self, **kwargs):
        from respond.models import get_month_file_name
        month_tables = self.month_record.month_table_files.all()
        for month_table in month_tables:
            month_table.inserted = True
            file_name = get_month_file_name(month_table)
            month_table.file = file_name
            month_table.save()

    def validate_temp_tables_after(self, **kwargs):
        pass

    def indexing_temp_tables_after(self, **kwargs):
        pass

    def save_cat_tables_after(self, **kwargs):
        pass

    def all_base_tables_saved(self, **kwargs):
        from django.utils import timezone
        self.month_record.last_pre_insertion = timezone.now()
        self.month_record.end_stage("pre_insert", self.base_task.main_task)
        self.month_record.save()

    def all_base_tables_validated(self, **kwargs):
        from django.utils import timezone
        import json
        self.month_record.last_validate = timezone.now()
        errors = self.month_record.end_stage(
            "validate", self.base_task.main_task)
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
        self.month_record.save()

    def all_base_tables_indexed(self, **kwargs):
        self.month_record.end_stage("indexing", self.base_task.main_task)
        self.month_record.save()

    def all_temp_tables_inserted(self, **kwargs):
        self.month_record.end_stage("insert", self.base_task.main_task)
        self.month_record.save()

    def save_lap_sheets_inserted(self, **kwargs):
        from respond.models import LapSheet
        child_task_errors = self.base_task.main_task.parent_task.child_tasks.filter(
            status_task__macro_status="with_errors")
        print("child_task_errors: ", child_task_errors)
        if not child_task_errors.exists():
            lap_sheets = LapSheet.objects.filter(
                cat_inserted=False, lap=0,
                sheet_file__month_records__in=[self.month_record],
            )
            lap_sheets.update(cat_inserted=True)
