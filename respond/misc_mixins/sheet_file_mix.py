from respond.models import SheetFile, LapSheet


class FromAws:

    def __init__(self, sheet_file: SheetFile, task_params=None):
        self.sheet_file = sheet_file
        self.task_params = task_params

    def check_success_insert(self, **kwargs):

        errors = kwargs.get("errors", [])
        if not errors:
            # self.save_csv_in_db_after(**kwargs)
            self.save_lap_cat_tables_after(**kwargs)
        self.sheet_file.save_stage('insert', errors)
        return [], errors, True

    # def save_csv_in_db_after(self, **kwargs):
    def save_lap_cat_tables_after(self, **kwargs):
        errors = kwargs.get("errors", [])
        # if not errors:
        #     table_files_ids = kwargs.get("table_files_ids", [])
        #     TableFile.objects\
        #         .filter(id__in=table_files_ids)\
        #         .update(inserted=True)
        return [], [], True

    def save_new_split_files(self, **kwargs):
        from respond.models import DataFile
        errors = kwargs.get("errors", [])
        if errors:
            return [], errors, True

        original_file = kwargs.get("original_file", None)
        new_files = kwargs.get("new_files", [])
        petition = self.sheet_file.data_file.petition_file_control.petition
        orphan_pet_control = petition.orphan_pet_control
        for file_name in new_files:
            provider = petition.real_provider or petition.agency.provider
            new_file = DataFile.objects.create(
                file=file_name,
                provider=provider,
                directory=f"intermediary_of_{original_file}",
                petition_file_control=orphan_pet_control,
            )
            new_file.finished_stage('initial|finished')
            print("new_file", new_file)
        self.sheet_file.save_stage("transform", errors)
        return [], errors, True

    def build_csv_data_from_aws(self, **kwargs):
        from django.utils import timezone
        from inai.models import MonthRecord
        from respond.misc_mixins.lap_sheet_mix import FromAws as LapSheetAws
        # print("FINISH BUILD CSV DATA")
        data_file = self.sheet_file.data_file
        is_prepare = kwargs.get("is_prepare", False)
        # sheet_file_id = kwargs.get("sheet_file_id", None)
        # sheet_file = SheetFile.objects.get(id=sheet_file_id)
        # print("is_prepare", is_prepare)
        next_lap = self.sheet_file.next_lap if not is_prepare else -1
        # print("next_lap", next_lap)
        # print("next_lap", sheet_file.next_lap)
        # print("final_paths", final_paths)
        report_errors = kwargs.get("report_errors", {})
        lap_sheet, created = LapSheet.objects.get_or_create(
            sheet_file=self.sheet_file, lap=next_lap)
        fields_in_report = report_errors.keys()
        for field in fields_in_report:
            setattr(lap_sheet, field, report_errors.get(field, 0))
        lap_sheet.last_edit = timezone.now()
        lap_sheet.save()

        if not is_prepare and not \
                data_file.petition_file_control.file_control.decode:
            decode = kwargs.get("decode", None)
            if decode:
                data_file.petition_file_control.file_control.decode = decode
                data_file.petition_file_control.file_control.save()

        error_fields = ["real_missing_rows", "missing_fields"]
        errors_count = sum([report_errors.get(field, 0) for field in error_fields])
        warnings_count = report_errors.get("warnings_fields", 0)
        total_rows = report_errors.get("total_count", 0) - report_errors.get("discarded_count", 0)
        errors = []
        if not total_rows:
            errors.append("No se encontraron filas")
        elif (errors_count - warnings_count) / total_rows > 0.05:
            errors.append("Se encontraron demasiados errores en filas/campos")
        stage_id = "prepare" if is_prepare else "transform"

        if is_prepare or errors:
            self.sheet_file.save_stage(stage_id, errors)
            return [], errors, True
        # data_file.all_results = kwargs.get("report_errors", {})
        # data_file.save()
        final_paths = kwargs.get("final_paths", []) or []
        lap_sheet_aws = LapSheetAws(lap_sheet)
        new_task, errors, data = lap_sheet_aws.save_result_csv(final_paths)

        all_months = kwargs.get("all_months", []) or []
        self.sheet_file.month_records.clear()
        self.sheet_file.year_month = None
        if len(all_months) == 0:
            errors.append("No se encontraron meses")
        else:
            year_months = []
            for ym in all_months:
                month = str(ym[1]).zfill(2)
                year_months.append(f"{ym[0]}-{month}")
                month_record = MonthRecord.objects.get_or_create(
                    provider=self.sheet_file.data_file.provider,
                    year_month=f"{ym[0]}-{month}")[0]
                self.sheet_file.month_records.add(month_record)
            # errors.append(f"Se encontraron demasiados meses: {all_months}")
        if len(all_months) == 1:
            ym = all_months[0]
            month = str(ym[1]).zfill(2)
            self.sheet_file.year_month = f"{ym[0]}-{month}"
        self.sheet_file.save_stage(stage_id, errors)
        return new_task, errors, data


def delete_extra_files():
    from respond.models import SheetFile, MonthRecord
    sheet_files = SheetFile.objects.filter(
        data_file__provider_id=53)
    all_month_records = MonthRecord.objects.filter(
        provider_id=53).values("year_month", "id")
    month_records_obj = {mr["year_month"]: mr["id"] for mr in all_month_records}
    for sheet_file in sheet_files:
        month_records = sheet_file.month_records.all()
        if len(month_records) > 1:
            if sheet_file.year_month:
                month_record_id = month_records_obj.get(sheet_file.year_month, None)
                if month_record_id:
                    sheet_file.month_records.clear()
                    sheet_file.month_records.add(month_record_id)
                    sheet_file.save()
                    continue
                else:
                    print("No se encontró el mes", sheet_file.year_month)
            else:
                # month_count = len(month_records)
                print("No se encontró un solo mes", sheet_file.id)



