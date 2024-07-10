from respond.models import DataFile


class FromAws:

    def __init__(self, data_file: DataFile, task_params=None):
        self.data_file = data_file
        self.task_params = task_params

    def decompress_gz_after(self, **kwargs):
        from respond.models import SheetFile
        from respond.views import SampleFile
        # import pathlib
        new_files = kwargs.get("new_files", {})
        # final_path = kwargs.get("final_path", {})
        # suffixes = pathlib.Path(final_path).suffixes
        sample_file = SampleFile()
        # generic_sample = {
        #     "all_data": kwargs.pop("all_data", []),
        #     "tail_data": kwargs.pop("tail_data", []),
        # }
        # sample_file.create_file(
        #     self, cat_name="default_samples", sample_data=generic_sample)
        decode = kwargs.get("decode")
        for sheet_file in new_files:
            final_path = sheet_file.pop("final_path")
            total_rows = sheet_file.pop("total_rows")
            sheet_name = sheet_file.pop("sheet_name")
            sample_path = sheet_file.pop("sample_path")
            sample_data = sample_file.get_json_content(sample_path)
            SheetFile.objects.get_or_create(
                data_file=self.data_file,
                file=final_path,
                file_type_id="split",
                sheet_name=sheet_name,
                total_rows=total_rows,
                # sample_data=generic_sample,
                # sample_file=sample_file.final_path,
                sample_data=sample_data,
                sample_file=sample_path,
            )
        if decode:
            file_control = self.data_file.petition_file_control.file_control
            if not file_control.decode and file_control.data_group_id != 'orphan':
                file_control.decode = decode
                file_control.save()
        return [], [], self.data_file

    def build_sample_data_after(self, parent_task=None, **kwargs):
        from respond.models import SheetFile
        from respond.views import SampleFile
        new_sheets = kwargs.get("new_sheets", {})
        sheet_count = len(new_sheets)
        sample_file = SampleFile()
        for sheet_name, sheet_details in new_sheets.items():
            is_not_xls = sheet_count == 1 and sheet_name == "default"
            simple_path = self.data_file.file if is_not_xls else None
            file_type_id = "clone" if is_not_xls else "sheet"
            final_path = sheet_details.pop("final_path", simple_path)
            total_rows = sheet_details.pop("total_rows")
            sample_path = sheet_details.pop("sample_path")
            sample_sheet = sample_file.get_json_content(sample_path)
            # sample_file.create_file(self, sample_sheet)
            SheetFile.objects.create(
                file=final_path,
                data_file=self.data_file,
                sheet_name=sheet_name,
                # sample_data=sample_sheet,
                # sample_file=sample_file.final_path,
                sample_data=sample_sheet,
                sample_file=sample_path,
                file_type_id=file_type_id,
                total_rows=total_rows
            )
        decode = kwargs.get("decode")
        if decode:
            file_control = self.data_file.petition_file_control.file_control
            if not file_control.decode and file_control.data_group_id != 'orphan':
                file_control.decode = decode
                file_control.save()
        if self.data_file.stage_id == "explore":
            self.data_file.status_id = "finished"
            self.data_file.save()
        return [], [], self.data_file
