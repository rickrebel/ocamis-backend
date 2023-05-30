from inai.models import EntityWeek


class FromAws:

    def __init__(self, entity_week: EntityWeek, task_params=None):
        self.entity_week = entity_week
        self.task_params = task_params

    def analyze_uniques_after(self, **kwargs):
        print("analyze_uniques_after---------------------------------")
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
        self.save_entity_week(unique_counts)
        errors = self.save_crossing_sheets(month_pairs, month_sheets)
        all_errors += errors

        return all_tasks, all_errors, True

    def save_merged_from_aws(self, **kwargs):
        from inai.models import TableFile, SheetFile
        from data_param.models import Collection
        base_models = ["drug", "rx"]
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
        return [], [], True

    def save_entity_week(self, month_week_counts):
        from django.utils import timezone
        self.entity_week.drugs_count = month_week_counts["drugs_count"]
        self.entity_week.rx_count = month_week_counts["rx_count"]
        self.entity_week.duplicates_count = month_week_counts["dupli"]
        self.entity_week.shared_count = month_week_counts["shared"]
        self.entity_week.last_transformation = timezone.now()
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
        from django.utils import timezone
        from inai.models import SheetFile, CrossingSheet
        print("start save_crossing_sheets", timezone.now())
        all_errors = []

        shared_pairs = month_pairs["shared"]
        edited_crosses = []

        for sheet_id, value in sheets.items():
            table_file = self.entity_week.table_files.filter(
                lap_sheet__lap=0, lap_sheet__sheet_file_id=sheet_id)
            if table_file.count() != 1:
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
            # current_sheet = SheetFile.objects.get(id=sheet_id)
            # if current_sheet.year_month != self.entity_week.year_month:
            #     continue
            # current_sheet.rx_count = value["rx_count"]
            # current_sheet.duplicates_count = value["dupli"]
            # current_sheet.shared_count = value["shared"]
            # current_sheet.save()
            table_file.update(
                rx_count=value["rx_count"],
                # drugs_count=value["drugs_count"],
                duplicates_count=value["dupli"],
                shared_count=value["shared"]
            )

        def same_year_month(cr):
            year_months = [cr.sheet_file_1.year_month, cr.sheet_file_2.year_month]
            some_is_same = self.entity_week.year_month in year_months
            if some_is_same:
                edited_crosses.append(cr.id)
            return some_is_same

        already_shared = set()
        for pair, value in month_pairs["dupli"].items():
            # shared_count = shared_pairs.pop(pair, 0)
            print("pair", pair)
            print("value", value)
            sheet_1, sheet_2 = pair.split("|")
            cross, created = CrossingSheet.objects.get_or_create(
                entity=self.entity_week.entity,
                sheet_file_1_id=sheet_1,
                sheet_file_2_id=sheet_2,
                iso_week=self.entity_week.iso_week,
                iso_year=self.entity_week.iso_year,
                year_week=self.entity_week.year_week,
                iso_delegation=self.entity_week.iso_delegation
            )
            # if not same_year_month(cross):
            #     continue
            shared_count = shared_pairs.get(pair, 0)
            if shared_count:
                already_shared.add(pair)

            cross.duplicates_count = value
            cross.shared_count = shared_count
            cross.last_crossing = timezone.now()
            # if not created:
            #     print("cross", cross)
            #     print("last_crossing", cross.last_crossing)
            #     print("!!!!!!!!!!!!!!!!!!!!!\n")
            cross.save()

        for pair, value in shared_pairs.items():
            if pair in already_shared:
                continue
            sheet_1, sheet_2 = pair.split("|")
            cross, created = CrossingSheet.objects.get_or_create(
                entity=self.entity_week.entity,
                sheet_file_1_id=sheet_1,
                sheet_file_2_id=sheet_2,
            )
            # if not same_year_month(cross):
            #     continue
            cross.duplicates_count = 0
            cross.shared_count = value
            cross.last_crossing = timezone.now()
            cross.save()

        return all_errors

        # year_month_crosses_1 = CrossingSheet.objects.filter(
        #     entity=self.entity_week.entity,
        #     sheet_file_1__year_month=self.entity_week.year_month)
        # year_month_crosses_2 = CrossingSheet.objects.filter(
        #     entity=self.entity_week.entity,
        #     sheet_file_2__year_month=self.entity_week.year_month)
        # year_month_crosses = year_month_crosses_1 | year_month_crosses_2
        # year_month_crosses = year_month_crosses.exclude(id__in=edited_crosses)
        # year_month_crosses.delete()
