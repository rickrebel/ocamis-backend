from task.aws.common import send_simple_response, BotoUtils


# def decompress_zip_aws(event, context):
def lambda_handler(event, context):

    decompress_gz = DecompressZip(event, context)
    suffixes = event.get("suffixes")
    upload_path = event.get("upload_path")
    result, errors = decompress_gz.decompress_file(suffixes, upload_path)

    return send_simple_response(event, context, errors, result)


class DecompressZip:

    def __init__(self, event: dict, context):
        self.context = context
        self.s3_utils = BotoUtils(event["s3"])
        file = event["file"]
        self.object_bytes = self.s3_utils.get_object_file(file, "zip")

    def decompress_file(self, suffixes, upload_path):
        import zipfile
        import rarfile

        result = {"files": []}
        if '.zip' in suffixes:
            zip_file = zipfile.ZipFile(self.object_bytes)
        elif '.rar' in suffixes:
            zip_file = rarfile.RarFile(self.object_bytes)
        else:
            return result, ["No se reconoce el formato del archivo"]

        for zip_elem in zip_file.infolist():
            if zip_elem.is_dir():
                continue
            pos_slash = zip_elem.filename.rfind("/")
            # only_name = zip_elem.filename[pos_slash + 1:]
            directory = (zip_elem.filename[:pos_slash]
                         if pos_slash > 0 else None)
            final_path = upload_path.replace(
                "NEW_FILE_NAME", zip_elem.filename)
            file_bytes = zip_file.open(zip_elem).read()
            self.s3_utils.save_file_in_aws(
                file_bytes, final_path, content_type=None)
            result["files"].append(
                {"file": final_path, "directory": directory})
        all_errors = self.s3_utils.errors
        return result, all_errors
