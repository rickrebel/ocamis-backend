from respond.models import ReplyFile, set_upload_reply_path
from task.builder import TaskBuilder
from inai.petition_mixins.petition_mix import PetitionTransformMix


class ReplyFileMixReal:

    def __init__(self, reply_file: ReplyFile, base_task: TaskBuilder = None):
        self.reply_file = reply_file
        self.base_task = base_task

    def decompress_reply(self):
        import pathlib

        suffixes = pathlib.Path(self.reply_file.final_path).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        # comprobate if is a zip file or a rar file
        is_zip_or_rar = suffixes.intersection({'.zip', '.rar'})
        if not is_zip_or_rar:
            error = "El archivo no es un archivo comprimido"
            self.base_task.add_errors([error], True, comprobate=True)
            return None
        file_name = f"rf_{self.reply_file.id}/NEW_FILE_NAME"
        upload_path = set_upload_reply_path(self.reply_file, file_name, "data")
        params = {
            "file": self.reply_file.file.name,
            "suffixes": list(suffixes),
            "upload_path": upload_path,
        }
        decompress_task = TaskBuilder(
            "decompress_zip_aws", parent_class=self.base_task,
            models=[self.reply_file], params=params)
        decompress_task.async_in_lambda()


class FromAws:

    def __init__(self, reply_file: ReplyFile, base_task: TaskBuilder = None):
        self.reply_file = reply_file
        self.base_task = base_task

    def decompress_zip_aws_after(self, **kwargs):
        print("decompress_zip_aws_after---------------------------------")
        # from inai.models import PetitionFileControl
        from respond.models import DataFile
        all_data_files_ids = []
        all_files = kwargs.get("files", [])
        orphan_pfc = self.reply_file.petition.get_orphan_pfc(forced_create=True)
        # print("all_files", all_files)
        petition = self.reply_file.petition
        provider = petition.real_provider or petition.agency.provider
        for data_file in all_files:
            new_file = DataFile.objects.create(
                file=data_file["file"],
                provider=provider,
                reply_file=self.reply_file,
                directory=data_file["directory"],
                petition_file_control=orphan_pfc,
            )
            new_file.finished_stage('initial|finished')
            all_data_files_ids.append(new_file.id)
            # print("new_file", new_file)
        # print("all_data_files_ids", all_data_files_ids)
        all_data_files = DataFile.objects.filter(id__in=all_data_files_ids)\
            .prefetch_related("petition_file_control")

        petition_class = PetitionTransformMix(
            petition, all_data_files, base_task=self.base_task)
        petition_class.find_matches_for_data_files()
