
class ReplyFileMix:
    final_path: str
    file: None
    id: int
    petition: None

    def decompress(self, pet_file_ctrl, task_params=None):
        import pathlib
        from inai.models import set_upload_path
        from respond.models import DataFile
        from task.serverless import async_in_lambda

        if DataFile.objects.filter(reply_file=self).exists():
            return None
        suffixes = pathlib.Path(self.final_path).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        # comprobate if is a zip file or a rar file
        is_zip_or_rar = suffixes.intersection({'.zip', '.rar'})
        if not is_zip_or_rar:
            return None
        upload_path = set_upload_path(self, f"reply_file_{self.id}/NEW_FILE_NAME")
        params = {
            "file": self.file.name,
            "suffixes": list(suffixes),
            "upload_path": upload_path,
        }
        task_params = task_params or {}
        task_params["models"] = [self]
        params_after = task_params.get("params_after", {})
        params_after["pet_file_ctrl_id"] = pet_file_ctrl.id
        task_params["params_after"] = params_after
        async_task = async_in_lambda("decompress_zip_aws", params, task_params)
        # print async_task
        return async_task

    def decompress_zip_aws_after(self, task_params=None, **kwargs):
        print("decompress_zip_aws_after---------------------------------")
        from inai.models import PetitionFileControl
        from respond.models import DataFile
        # print("kwargs", kwargs)
        errors = []
        parent_task = task_params.get("parent_task")
        params_after = parent_task.params_after
        pet_file_ctrl_id = params_after["pet_file_ctrl_id"]
        # pet_file_ctrl_id = kwargs.get("pet_file_ctrl")
        if "errorMessage" in kwargs:
            errors.append(kwargs["errorMessage"])
            return None, errors
        if kwargs.get('errors'):
            errors += kwargs['errors']
        all_data_files_ids = []
        pet_file_ctrl = PetitionFileControl.objects.get(id=pet_file_ctrl_id)
        all_files = kwargs.get("files", [])
        print("all_files", all_files)
        for data_file in all_files:
            entity = self.petition.real_provider or self.petition.agency.entity
            new_file = DataFile.objects.create(
                file=data_file["file"],
                entity=entity,
                reply_file=self,
                directory=data_file["directory"],
                petition_file_control=pet_file_ctrl,
            )
            new_file.finished_stage('initial|finished')
            all_data_files_ids.append(new_file.id)
            # print("new_file", new_file)
        print("all_data_files_ids", all_data_files_ids)
        all_data_files = DataFile.objects.filter(id__in=all_data_files_ids)\
            .prefetch_related("petition_file_control")
        print("all_data_files", all_data_files)
        all_tasks, new_errors = self.petition.find_matches_in_children(
            all_data_files, task_params=task_params)
        errors += new_errors
        return all_tasks, errors, None
