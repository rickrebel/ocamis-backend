from inai.misc_mixins.month_record_mix import MonthRecordMix


class FromAws(MonthRecordMix):

    def revert_stages_after(self, **kwargs):
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
