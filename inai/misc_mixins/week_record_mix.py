from inai.models import WeekRecord
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, week_record: WeekRecord, base_task: TaskBuilder = None):
        self.week_record = week_record
        self.split_by_delegation = week_record.provider.split_by_delegation
        self.base_task = base_task

    def analyze_uniques_after(self, **kwargs):
        print("analyze_uniques_after---------------------------------")
        # RICK TASK2: Estos errores deberíamos ponerlos en otro campo y
        # sacarlos desde el principio
        if self.base_task.errors:
            pass
        unique_counts = kwargs.get("month_week_counts", {})
        month_pairs = kwargs.get("month_pairs", {})
        month_sheets = kwargs.get("month_sheets", {})
        self._save_week_record(unique_counts, month_pairs)
        self._save_crossing_sheets(month_sheets)

    # def save_csv_in_db_after(self, **kwargs):
    def save_week_base_models_after(self, **kwargs):
        pass
        # from django.utils import timezone
        # self.week_record.last_insertion = timezone.now()
        # RICK TASK2: Esto debería estar estandarizado
        # if not self.base_task.errors:
        #     table_files_ids = kwargs.get("table_files_ids", [])
        #     TableFile.objects\
        #         .filter(id__in=table_files_ids)\
        #         .update(inserted=True)

    def save_merged_from_aws(self, **kwargs):
        from django.utils import timezone
        from respond.models import TableFile
        from data_param.models import Collection
        base_models = [
            "drug", "rx", "complement_drug", "complement_rx", "diagnosis_rx"]
        new_table_files = []
        drugs_count = kwargs.get("drugs_count", 0)
        for model in base_models:
            file_path = kwargs.get(f"{model}_path")
            if not file_path:
                continue
            collection = Collection.objects.get(snake_name=model)
            table_file, c = TableFile.objects.get_or_create(
                # week_record=self.week_record,
                provider=self.week_record.provider,
                iso_week=self.week_record.iso_week,
                iso_year=self.week_record.iso_year,
                year_week=self.week_record.year_week,
                iso_delegation=self.week_record.iso_delegation,
                month=self.week_record.month,
                year=self.week_record.year,
                year_month=self.week_record.year_month,
                week_record=self.week_record,
                collection=collection)
            table_file.file = file_path
            if model == "drug":
                table_file.drugs_count = drugs_count
            table_file.save()
            new_table_files.append(table_file)
        self.week_record.deliveries.all().delete()
        sums_by_delivered = kwargs.get("sums_by_delivered", {})
        for delivered, count in sums_by_delivered.items():
            self.week_record.deliveries.create(
                delivered_id=delivered, value=count)
            # setattr(self.week_record, delivered, count)
        self.week_record.last_merge = timezone.now()
        self.week_record.drugs_count = drugs_count
        self.week_record.save()

    def rebuild_week_csv_after(self, **kwargs):
        from respond.models import TableFile
        drugs_count = kwargs.get("drugs_count", 0)
        table_file = TableFile.objects.get(
            week_record=self.week_record,
            collection__snake_name="drug")
        table_file.drugs_count = drugs_count
        table_file.save()
        self.week_record.drugs_count = drugs_count
        return [], [], True

    def _save_week_record(self, month_week_counts, month_pairs):
        from django.utils import timezone
        # duplicates_count
        fields = [
            ["drugs_count", "drugs_count"],
            ["rx_count", "rx_count"],
            ["duplicates_count", "dupli"],
            ["shared_count", "shared"],
        ]
        for field in fields:
            setattr(self.week_record, field[0], month_week_counts[field[1]])
        self.week_record.crosses = month_pairs
        # self.week_record.drugs_count = month_week_counts["drugs_count"]
        # self.week_record.rx_count = month_week_counts["rx_count"]
        # self.week_record.duplicates_count = month_week_counts["dupli"]
        # self.week_record.shared_count = month_week_counts["shared"]
        self.week_record.last_crossing = timezone.now()
        self.week_record.save()
        # current_month_records = MonthRecord.objects.filter(
        #     provider_id=self.week_record.provider_id,
        #     year_month=self.week_record.year_month)
        # current_month_records.update(
        #     duplicates_count=month_counts["dupli"],
        #     shared_count=month_counts["shared"],
        #     rx_count=month_counts["rx_count"],
        #     drugs_count=month_counts["drugs_count"]
        # )

    def _save_crossing_sheets(self, sheets):
        from respond.models import TableFile

        table_files = self.week_record.table_files.filter(
            lap_sheet__lap=0)

        for table_file in table_files:
            sheet_id = table_file.lap_sheet.sheet_file_id
            sheet_id = str(sheet_id)
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
