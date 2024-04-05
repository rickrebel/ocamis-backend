from respond.models import LapSheet, TableFile
from inai.models import WeekRecord


class FromAws:

    def __init__(self, lap_sheet: LapSheet, task_params=None):
        self.lap_sheet = lap_sheet
        self.task_params = task_params

    def save_result_csv(self, result_files):
        from data_param.models import Collection
        from inai.models import MonthRecord
        from django.utils import timezone

        new_tasks = []
        all_errors = []
        provider = self.lap_sheet.sheet_file.data_file.provider
        optional_fields = [
            "iso_year", "iso_week", "year_week", "iso_delegation_id",
            "year", "month", "year_month"]
        count_fields = ["drugs_count", "rx_count"]
        all_year_months = set()
        all_month_records = MonthRecord.objects.filter(provider=provider)\
            .values("id", "year_month")
        values_to_weeks = optional_fields.copy()
        values_to_weeks.extend(["month_record_id"])
        all_week_records = WeekRecord.objects\
            .filter(provider=provider).values(*["id"] + values_to_weeks)
        dict_week_records = {}
        for week_record in all_week_records:
            concat_id = []
            for field in values_to_weeks:
                concat_id.append(week_record[field])
            string_id = "_".join([str(x) for x in concat_id])
            dict_week_records[string_id] = week_record["id"]

        TableFile.objects\
            .filter(lap_sheet=self.lap_sheet, inserted=False)\
            .delete()
        new_table_files = []
        week_records_ids = []
        for result_file in result_files:
            model_name = result_file.get("model")
            # print("model_name", model_name)
            query_create = {"provider": provider, "file": result_file["path"]}
            concat_id = []
            # query_create = {"provider": provider}
            # query_update = {"file": result_file["path"]}
            if not model_name:
                year_month = result_file.get("year_month")
                try:
                    month_record_id = all_month_records.get(
                        year_month=year_month)["id"]
                except Exception as e:
                    all_errors.append(
                        f"Error al obtener el mes {year_month} - {e}")
                    continue
                all_year_months.add(year_month)
                query_create_week = {}
                for field in optional_fields:
                    value = result_file.get(field, None)
                    query_create_week[field] = value
                    if field == "month_record_id":
                        concat_id.append(month_record_id)
                    else:
                        concat_id.append(value)
                        query_create[field] = value
                for field in count_fields:
                    query_create[field] = result_file.get(field, 0)
                string_id = "_".join([str(x) for x in concat_id])
                week_record_id = dict_week_records.get(string_id, None)
                if week_record_id:
                    week_records_ids.append(week_record_id)
                else:
                    query_create_week["provider"] = provider
                    query_create_week["month_record_id"] = month_record_id
                    try:
                        week_record, created = WeekRecord.objects.get_or_create(
                            **query_create_week)
                        week_record_id = week_record.id
                        week_records_ids.append(week_record_id)
                    except Exception as e:
                        all_errors.append(
                            f"Error al crear la semana {query_create_week} - {e}")
                        continue
                query_create["week_record_id"] = week_record_id
            else:
                collection = Collection.objects.get(model_name=model_name)
                query_create["collection"] = collection
            query_create["lap_sheet"] = self.lap_sheet
            table_file = TableFile(**query_create)
            new_table_files.append(table_file)

        TableFile.objects.bulk_create(new_table_files)

        MonthRecord.objects\
            .filter(year_month__in=list(all_year_months), provider=provider)\
            .update(last_transformation=timezone.now())

        WeekRecord.objects\
            .filter(id__in=week_records_ids, provider=provider)\
            .update(last_transformation=timezone.now())

        # return new_tasks, all_errors, all_new_files
        return new_tasks, all_errors, True

    def save_result_csv_prev(self, result_files):
        from data_param.models import Collection
        from respond.models import TableFile
        from inai.models import MonthRecord, WeekRecord
        from django.utils import timezone

        all_new_files = []
        new_tasks = []
        new_file_ids = []
        provider = self.lap_sheet.sheet_file.data_file.provider
        optional_fields = [
            "iso_year", "iso_week", "year_week", "iso_delegation",
            "year", "month", "year_month"]
        count_fields = ["drugs_count", "rx_count"]
        all_year_months = set()
        all_complex_dates = set()
        for result_file in result_files:
            model_name = result_file.get("model")
            # print("model_name", model_name)
            query_create = {"provider": provider}
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
                query_create_week["provider"] = provider
                month_record = MonthRecord.objects.filter(
                    year_month=year_month, provider=provider).first()
                query_create_week["month_record"] = month_record
                week_record, created = WeekRecord.objects.get_or_create(
                    **query_create_week)
                week_record.last_transformation = timezone.now()
                week_record.save()
                query_create["week_record"] = week_record
            else:
                collection = Collection.objects.get(model_name=model_name)
                query_create["collection"] = collection
            query_create["lap_sheet"] = self.lap_sheet
            table_file, created = TableFile.objects.get_or_create(
                **query_create)
            new_file_ids.append(table_file.id)
            table_file.__dict__.update(**query_update)
            # table_file.file = result_file["path"]
            # table_file.save()
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

        MonthRecord.objects\
            .filter(year_month__in=list(all_year_months), provider=provider)\
            .update(last_transformation=timezone.now())

        return new_tasks, [], all_new_files

    # def confirm_all_inserted(self):
    #     pending_tables = self.lap_sheet.table_files.filter(inserted=False).exists()
    #     self.inserted = None if pending_tables else True
    #     self.save()
    #     return not pending_tables
