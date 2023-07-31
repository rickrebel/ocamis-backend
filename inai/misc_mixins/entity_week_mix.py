from inai.models import EntityWeek


class FromAws:

    def __init__(self, entity_week: EntityWeek, task_params=None):
        self.entity_week = entity_week
        self.split_by_delegation = entity_week.entity.split_by_delegation
        self.task_params = task_params

    def analyze_uniques_after(self, **kwargs):
        # print("analyze_uniques_after---------------------------------")
        # print("kwargs", kwargs)
        all_errors = []
        # parent_task = task_params.get("parent_task")
        # params_after = parent_task.params_after
        all_tasks = []
        if kwargs.get('errors'):
            all_errors += kwargs['errors']
        unique_counts = kwargs.get("month_week_counts", {})
        month_pairs = kwargs.get("month_pairs", {})
        month_sheets = kwargs.get("month_sheets", {})
        self.save_entity_week(unique_counts, month_pairs)
        errors = self.save_crossing_sheets(month_pairs, month_sheets)
        all_errors += errors

        return all_tasks, all_errors, True

    # def save_csv_in_db_after(self, **kwargs):
    def save_week_base_models_after(self, **kwargs):
        from inai.models import TableFile
        # from django.utils import timezone
        # self.entity_week.last_insertion = timezone.now()
        if kwargs.get("errors"):
            # self.entity_week.errors = True
            print("ERRORS", kwargs.get("errors"))
        # else:
        #     table_files_ids = kwargs.get("table_files_ids", [])
        #     TableFile.objects\
        #         .filter(id__in=table_files_ids)\
        #         .update(inserted=True)
        return [], [], True

    def save_merged_from_aws(self, **kwargs):
        from django.utils import timezone
        from inai.models import TableFile, SheetFile
        from inai.misc_mixins.entity_month_mix import FromAws as EntityMonthMix
        from data_param.models import Collection
        base_models = ["drug", "rx"]
        new_table_files = []
        for model in base_models:
            file_path = kwargs.get(f"{model}_path")
            collection = Collection.objects.get(snake_name=model)
            table_file, c = TableFile.objects.get_or_create(
                # entity_week=self.entity_week,
                entity=self.entity_week.entity,
                iso_week=self.entity_week.iso_week,
                iso_year=self.entity_week.iso_year,
                year_week=self.entity_week.year_week,
                iso_delegation=self.entity_week.iso_delegation,
                month=self.entity_week.month,
                year=self.entity_week.year,
                year_month=self.entity_week.year_month,
                entity_week=self.entity_week,
                collection=collection)
            table_file.file = file_path
            table_file.save()
            new_table_files.append(table_file)
        sums_by_delivered = kwargs.get("sums_by_delivered", {})
        for delivered, count in sums_by_delivered.items():
            setattr(self.entity_week, delivered, count)
        self.entity_week.last_merge = timezone.now()
        self.entity_week.drugs_count = kwargs.get("drugs_count", 0)
        self.entity_week.save()
        return [], [], True

    def rebuild_week_csv_after(self, **kwargs):
        from inai.models import TableFile
        drugs_count = kwargs.get("drugs_count", 0)
        table_file = TableFile.objects.get(
            entity_week=self.entity_week,
            collection__snake_name="drug")
        table_file.drugs_count = drugs_count
        table_file.save()
        self.entity_week.drugs_count = drugs_count
        return [], [], True

    def save_entity_week(self, month_week_counts, month_pairs):
        from django.utils import timezone
        # duplicates_count
        fields = [
            ["drugs_count", "drugs_count"],
            ["rx_count", "rx_count"],
            ["duplicates_count", "dupli"],
            ["shared_count", "shared"],
        ]
        for field in fields:
            setattr(self.entity_week, field[0], month_week_counts[field[1]])
        self.entity_week.crosses = month_pairs
        # self.entity_week.drugs_count = month_week_counts["drugs_count"]
        # self.entity_week.rx_count = month_week_counts["rx_count"]
        # self.entity_week.duplicates_count = month_week_counts["dupli"]
        # self.entity_week.shared_count = month_week_counts["shared"]
        self.entity_week.last_crossing = timezone.now()
        self.entity_week.save()
        # current_entity_months = EntityMonth.objects.filter(
        #     entity_id=self.entity_week.entity_id,
        #     year_month=self.entity_week.year_month)
        # current_entity_months.update(
        #     duplicates_count=month_counts["dupli"],
        #     shared_count=month_counts["shared"],
        #     rx_count=month_counts["rx_count"],
        #     drugs_count=month_counts["drugs_count"]
        # )

    def save_crossing_sheets(self, month_pairs, sheets):
        from inai.models import TableFile
        all_errors = []

        table_files = self.entity_week.table_files.filter(
            lap_sheet__lap=0)

        for table_file in table_files:
            sheet_id = table_file.lap_sheet.sheet_file_id
            if sheet_id not in sheets:
                continue
            value = sheets[sheet_id]
            table_file.rx_count = value["rx_count"]
            table_file.duplicates_count = value["dupli"]
            table_file.shared_count = value["shared"]

        TableFile.objects.bulk_update(
            table_files,
            ["rx_count", "duplicates_count", "shared_count"]
        )

        return all_errors

    def save_crossing_sheets_old(self, month_pairs, sheets):
        all_errors = []

        for sheet_id, value in sheets.items():
            table_file = self.entity_week.table_files.filter(
                lap_sheet__lap=0,
                lap_sheet__sheet_file_id=sheet_id)
            if self.split_by_delegation:
                pass
            elif table_file.count() != 1:
                if table_file.count() == 0:
                    error = f"No existe ningún table_file "
                else:
                    error = f"Existen {table_file.count()} table_files"
                error += f" para sheet_id {sheet_id}, " \
                    f"semana {self.entity_week.iso_week} " \
                    f"año {self.entity_week.iso_year}, " \
                    f"year_month {self.entity_week.year_month}"
                all_errors.append(error)
                continue
            table_file.update(
                rx_count=value["rx_count"],
                # drugs_count=value["drugs_count"],
                duplicates_count=value["dupli"],
                shared_count=value["shared"]
            )

        return all_errors
