

class PetitionProcessMix:

    def decompress_process_files_first(self, pet_file_ctrl):
        import zipfile
        import rarfile
        import pathlib
        from django.conf import settings

        from inai.models import ProcessFile, DataFile
        from io import BytesIO
        from scripts.common import get_file, start_session, create_file
        all_errors = []

        is_prod = getattr(settings, "IS_PRODUCTION", False)

        s3_client = None
        dev_resource = None
        if is_prod:
            s3_client, dev_resource = start_session()

        process_files = ProcessFile.objects.filter(
            petition=self, has_data=True)
        for process_file in process_files:
            if DataFile.objects.filter(process_file=process_file).exists():
                continue
            suffixes = pathlib.Path(process_file.final_path).suffixes
            suffixes = set([suffix.lower() for suffix in suffixes])
            if is_prod:
                bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
                zip_obj = dev_resource.Object(
                    bucket_name=bucket_name,
                    key=f"{settings.AWS_LOCATION}/{process_file.file.name}"
                )
                buffer = BytesIO(zip_obj.get()["Body"].read())
            else:
                buffer = get_file(process_file, dev_resource)
            if '.zip' in suffixes:
                zip_file = zipfile.ZipFile(buffer)
            elif '.rar' in suffixes:
                zip_file = rarfile.RarFile(buffer)
            else:
                continue

            for zip_elem in zip_file.infolist():
                if zip_elem.is_dir():
                    continue
                pos_slash = zip_elem.filename.rfind("/")
                only_name = zip_elem.filename[pos_slash + 1:]
                directory = (zip_elem.filename[:pos_slash]
                             if pos_slash > 0 else None)
                file_bytes = zip_file.open(zip_elem).read()

                curr_file, file_errors = create_file(
                    process_file, file_bytes, only_name, s3_client=s3_client)
                if file_errors:
                    all_errors += file_errors
                    continue

                new_file = DataFile.objects.create(
                    file=curr_file,
                    process_file=process_file,
                    directory=directory,
                    petition_file_control=pet_file_ctrl,
                )
                new_file.change_status('initial')
        return all_errors

    def decompress_process_files(self, pet_file_ctrl):
        import pathlib
        from django.conf import settings
        from inai.models import ProcessFile, DataFile
        from scripts.common import build_s3
        from inai.models import set_upload_path
        from scripts.serverless import decompress_zip_aws, execute_in_lambda
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
            print("new_data_files", new_data_files)
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

