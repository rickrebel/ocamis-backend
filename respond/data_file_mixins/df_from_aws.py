from respond.models import DataFile
from task.base_views import TaskBuilder
from respond.data_file_mixins.find_coincidences import MatchControls


class FromAws:

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):
        self.data_file = data_file
        self.base_task = base_task
        self.task_params = {"parent_task": base_task.main_task}

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
                file_type="split",
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

    def build_sample_data_after(self, **kwargs):
        from respond.models import SheetFile
        from respond.views import SampleFile
        new_sheets = kwargs.get("new_sheets", {})
        sheet_count = len(new_sheets)
        sample_file = SampleFile()
        for sheet_name, sheet_details in new_sheets.items():
            is_not_xls = sheet_count == 1 and sheet_name == "default"
            simple_path = self.data_file.file if is_not_xls else None
            file_type = "clone" if is_not_xls else "sheet"
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
                file_type=file_type,
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

    # Función de after y directa
    # antes llamado find_matches_in_file_controls
    def find_matches_between_controls(
            self, task_params=None, provider_file_controls=None, **kwargs):
        from data_param.views import get_related_file_controls
        from data_param.models import FileControl
        kwargs = self._corroborate_save_data(task_params, **kwargs)
        if not provider_file_controls:
            provider_controls_ids = kwargs.get("provider_controls_ids", [])
            if not provider_controls_ids:
                provider_file_controls = get_related_file_controls(
                    data_file=self.data_file)
            else:
                provider_file_controls = FileControl.objects.filter(
                    id__in=provider_controls_ids)
        match_controls = MatchControls(self.data_file, self.base_task)
        saved = match_controls.find_in_file_controls(provider_file_controls)
        # for file_ctrl in provider_file_controls:
        #     saved = match_controls.find_file_controls(file_control=file_ctrl)
        #     all_errors.extend(match_controls.errors)
        errors = None
        if not saved:
            errors = ["No existe ningún grupo de control coincidente"]
            self.data_file.save_errors(errors, "cluster|with_errors")
        return None, errors, None

    # Función de after
    def find_coincidences_from_aws(self, task_params=None, **kwargs):
        self._corroborate_save_data(task_params, **kwargs)
        # saved, errors = self._find_coincidences(saved=False)
        match_controls = MatchControls(self.data_file, self.base_task)
        saved = match_controls.match_file_control()
        errors = match_controls.errors
        if not saved and not errors:
            errors = ["No coincide con el formato del archivo 3"]
        if errors:
            self.data_file.save_errors(errors, "explore|with_errors")
            return [], errors, None
        elif self.data_file.stage_id == 'cluster':
            self.data_file.finished_stage("cluster|finished")
        return [], errors, None

    def _corroborate_save_data(self, task_params=None, **kwargs):
        from_aws = kwargs.get("from_aws", False)
        print("from_aws", from_aws)

        if from_aws:
            # x, y, data_file = self.build_sample_data_after(**kwargs)
            self.build_sample_data_after(**kwargs)
            parent_task = task_params.get("parent_task", None)
            if parent_task.params_after:
                kwargs.update(parent_task.params_after)
        return kwargs
