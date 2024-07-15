from respond.models import ReplyFile
from task.base_views import TaskBuilder
from inai.petition_mixins.petition_mix import PetitionTransformsMixReal


class ReplyFileMixReal:

    def __init__(self, reply_file: ReplyFile, base_task: TaskBuilder = None):
        self.reply_file = reply_file
        self.task_params = {"parent_task": base_task.main_task}
        self.base_task = base_task

    def decompress_reply(self, pet_file_ctrl):
        import pathlib
        from inai.models import set_upload_path

        suffixes = pathlib.Path(self.reply_file.final_path).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        # comprobate if is a zip file or a rar file
        is_zip_or_rar = suffixes.intersection({'.zip', '.rar'})
        if not is_zip_or_rar:
            error = "El archivo no es un archivo comprimido"
            self.base_task.add_errors([error], True, comprobate=True)
            return None
        file_name = f"reply_file_{self.reply_file.id}/NEW_FILE_NAME"
        upload_path = set_upload_path(self.reply_file, file_name)
        params = {
            "file": self.reply_file.file.name,
            "suffixes": list(suffixes),
            "upload_path": upload_path,
        }
        params_after = {"pet_file_ctrl_id": pet_file_ctrl.id}
        decompress_task = TaskBuilder(
            function_name="decompress_zip_aws", parent_class=self.base_task,
            models=[self.reply_file], params_after=params_after, params=params)
        decompress_task.async_in_lambda(comprobate=True)


class FromAws:

    def __init__(self, reply_file: ReplyFile, task_params=None,
                 base_task: TaskBuilder = None):
        self.reply_file = reply_file
        self.task_params = task_params
        self.base_task = base_task

    def decompress_zip_aws_after(self, **kwargs):
        print("decompress_zip_aws_after---------------------------------")
        from inai.models import PetitionFileControl
        from respond.models import DataFile
        # print("kwargs", kwargs)
        params_after = self.base_task.main_task.params_after or {}
        pet_file_ctrl_id = params_after["pet_file_ctrl_id"]
        # RICK TASK: No contemplamos errorMessage en ningún lugar
        # if "errorMessage" in kwargs:
        #     errors.append(kwargs["errorMessage"])
        #     return None, errors
        # RICK TASK: No contemplamos errores en ningún lugar
        if new_errors := kwargs.get('errors'):
            # errors += kwargs['errors']
            self.base_task.add_errors(new_errors, True, comprobate=False)
        all_data_files_ids = []
        pet_file_ctrl = PetitionFileControl.objects.get(id=pet_file_ctrl_id)
        all_files = kwargs.get("files", [])
        # print("all_files", all_files)
        petition = self.reply_file.petition
        provider = petition.real_provider or petition.agency.provider
        for data_file in all_files:
            new_file = DataFile.objects.create(
                file=data_file["file"],
                provider=provider,
                reply_file=self.reply_file,
                directory=data_file["directory"],
                petition_file_control=pet_file_ctrl,
            )
            new_file.finished_stage('initial|finished')
            all_data_files_ids.append(new_file.id)
            # print("new_file", new_file)
        # print("all_data_files_ids", all_data_files_ids)
        all_data_files = DataFile.objects.filter(id__in=all_data_files_ids)\
            .prefetch_related("petition_file_control")

        petition_class = PetitionTransformsMixReal(
            petition, base_task=self.base_task)
        petition_class.find_matches_for_data_files(all_data_files)
        return self.base_task.new_tasks, self.base_task.errors, None
