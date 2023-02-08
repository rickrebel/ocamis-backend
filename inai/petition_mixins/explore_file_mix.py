

class PetitionProcessMix:

    def decompress_process_files(self, pet_file_ctrl):
        import pathlib
        from django.conf import settings
        from inai.models import ProcessFile, DataFile
        from scripts.common import build_s3
        from inai.models import set_upload_path
        from scripts.serverless import async_in_lambda, execute_in_lambda
        all_errors = []

        process_files = ProcessFile.objects.filter(
            petition=self, has_data=True)
        base_s3 = build_s3()
        for process_file in process_files:
            if DataFile.objects.filter(process_file=process_file).exists():
                continue
            suffixes = pathlib.Path(process_file.final_path).suffixes
            suffixes = set([suffix.lower() for suffix in suffixes])
            # comprobate if is a zip file or a rar file
            is_zip_or_rar = suffixes.intersection({'.zip', '.rar'})
            if not is_zip_or_rar:
                continue
            params = {
                "file": process_file.file.name,
                "s3": base_s3,
                "suffixes": list(suffixes),
                "process_file_id": process_file.id,
                "upload_path": set_upload_path(process_file, "NEW_FILE_NAME"),
            }
            #new_data_files = decompress_zip_aws(params, None)
            new_data_files = execute_in_lambda("decompress_zip_aws", params)
            #new_data_files = async_in_lambda("decompress_zip_aws", params)
            #print("new_data_files", new_data_files)
            if "errorMessage" in new_data_files:
                all_errors.append(new_data_files["errorMessage"])
                continue
            if new_data_files['errors']:
                all_errors += new_data_files['errors']
            for data_file in new_data_files['files']:
                new_file = DataFile.objects.create(
                    file=data_file["file"],
                    process_file=process_file,
                    directory=data_file["directory"],
                    petition_file_control=pet_file_ctrl,
                )
                new_file.change_status('initial')
                print("new_file", new_file)
        return all_errors

