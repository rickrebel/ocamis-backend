from respond.models import LapSheet, TableFile
from inai.models import WeekRecord
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, lap_sheet: LapSheet, base_task: TaskBuilder = None):
        self.lap_sheet = lap_sheet
        self.base_task = base_task

    def save_result_csv(self, result_files):
        from data_param.models import Collection
        from inai.models import MonthRecord
        from django.utils import timezone

        provider = self.lap_sheet.sheet_file.data_file.provider
        # RICK TableFile: Es un relajo, hay que estandarizarlo
        # optional_fields = ["iso_delegation_id"]
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
                    error = f"Error al obtener el mes {year_month} - {e}"
                    self.base_task.add_errors([error], comprobate=False)
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
                        error = f"Error al crear la semana {query_create_week} - {e}"
                        self.base_task.add_errors([error], comprobate=False)
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
