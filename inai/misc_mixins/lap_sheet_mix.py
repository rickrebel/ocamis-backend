from inai.models import LapSheet


class FromAws:

    def __init__(self, lap_sheet: LapSheet, task_params=None):
        self.lap_sheet = lap_sheet
        self.task_params = task_params

    def save_result_csv(self, result_files):
        from data_param.models import Collection
        from inai.models import TableFile, EntityMonth, EntityWeek
        from django.utils import timezone

        all_new_files = []
        new_tasks = []
        new_file_ids = []
        entity = self.lap_sheet.sheet_file.data_file.entity
        optional_fields = [
            "iso_year", "iso_week", "year_week", "iso_delegation",
            "year", "month", "year_month"]
        count_fields = ["drugs_count", "rx_count"]
        all_year_months = set()
        all_complex_dates = set()
        for result_file in result_files:
            model_name = result_file.get("model")
            # print("model_name", model_name)
            query_create = {"entity": entity}
            query_update = {"file": result_file["path"]}
            if not model_name:
                complex_date = tuple()
                year_month = result_file.get("year_month")
                query_create["year_month"] = year_month
                all_year_months.add(year_month)
                for field in optional_fields:
                    value = result_file.get(field, None)
                    query_create[field] = value
                    complex_date += (value,)
                for field in count_fields:
                    query_update[field] = result_file.get(field, 0)
                all_complex_dates.add(complex_date)
                query_create_week = query_create.copy()
                query_create_week["entity"] = entity
                entity_month = EntityMonth.objects.filter(
                    year_month=year_month, entity=entity).first()
                query_create_week["entity_month"] = entity_month
                entity_week, created = EntityWeek.objects.get_or_create(
                    **query_create_week)
                entity_week.last_transformation = timezone.now()
                entity_week.save()
                query_create["entity_week"] = entity_week
            else:
                collection = Collection.objects.get(model_name=model_name)
                query_create["collection"] = collection
            query_create["lap_sheet"] = self.lap_sheet
            table_file, created = TableFile.objects.get_or_create(
                **query_create)
            new_file_ids.append(table_file.id)
            table_file.__dict__.update(**query_update)
            # table_file.file = result_file["path"]
            table_file.save()
            # new_file.change_status('initial|finished')
            all_new_files.append(table_file)
            # new_tasks = self.lap_sheet.send_csv_to_db(result_file["path"], model_name)
            # new_tasks.append(new_tasks)
        TableFile.objects.filter(lap_sheet=self.lap_sheet)\
                         .exclude(id__in=new_file_ids)\
                         .delete()

        # def iso_to_gregorian(iso_year, iso_week, iso_day):
        #     import datetime
        #     fourth_jan = datetime.date(iso_year, 1, 4)
        #     _, fourth_jan_week, fourth_jan_day = fourth_jan.isocalendar()
        #     return fourth_jan + datetime.timedelta(
        #         days=iso_day - fourth_jan_day, weeks=iso_week - fourth_jan_week)

        # all_months = set()
        # for complex_date in all_weeks:
        #     iso_year, iso_week, year, month, year_month, delegation = complex_date
        #     date_init = iso_to_gregorian(year, week, 1)
        #     month = date_init.month
        #     year_gregorian = date_init.year
        #     year_month = f"{year_gregorian}-{month:02d}"
        #     all_months.add(year_month)

        EntityMonth.objects\
            .filter(year_month__in=list(all_year_months), entity=entity)\
            .update(last_transformation=timezone.now())

        return new_tasks, [], all_new_files

    # def confirm_all_inserted(self):
    #     pending_tables = self.lap_sheet.table_files.filter(inserted=False).exists()
    #     self.inserted = None if pending_tables else True
    #     self.save()
    #     return not pending_tables
