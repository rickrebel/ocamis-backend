from task.aws.common import BotoUtils, send_simple_response_2
import zipfile
import rarfile
rarfile.UNRAR_TOOL = '/opt/bin/unrar2'


# def decompress_zip_aws(event, context):
def lambda_handler(event, context):

    decompress_zip = DecompressZip(event, context)
    suffixes = event.get("suffixes")
    upload_path = event.get("upload_path")
    decompress_zip.decompress_file(suffixes, upload_path)
    # return send_simple_response(event, context, errors, result)
    decompress_zip.result["errors"] = decompress_zip.errors + \
        decompress_zip.s3_utils.errors
    return send_simple_response_2(event, context, decompress_zip.result)


class DecompressZip:

    def __init__(self, event: dict, context):
        self.context = context
        self.result = {"files": [], "errors": []}
        self.errors = []
        self.s3_utils = BotoUtils(event["s3"])
        file = event["file"]
        self.object_bytes = self.s3_utils.get_object_file(file, "zip")

    def decompress_file(self, suffixes, upload_path, prev_directory=None, object_bytes=None):
        from io import BytesIO
        if not object_bytes:
            object_bytes = self.object_bytes
        if '.zip' in suffixes:
            zip_file = zipfile.ZipFile(object_bytes)
        elif '.rar' in suffixes:
            zip_file = rarfile.RarFile(object_bytes)
        else:
            self.errors.append("No se reconoce el formato del archivo")
            return

        for zip_elem in zip_file.infolist():
            if zip_elem.is_dir():
                continue
            file_name = zip_elem.filename
            if "desktop.ini" in file_name:
                continue
            pos_slash = file_name.rfind("/")
            # only_name = file_name[pos_slash + 1:]
            directory = (file_name[:pos_slash]
                         if pos_slash > 0 else None)
            if prev_directory:
                directory = f"{prev_directory}/{directory}"
                file_name = f"{prev_directory}/{file_name}"
            # evaluate if file_name is a .zip or .rar file
            if file_name.endswith(".zip") or file_name.endswith(".rar"):
                object_bytes = zip_file.open(zip_elem).read()
                real_object_bytes = BytesIO(object_bytes)
                directory += f"/{file_name.replace('.', '_')}"
                self.decompress_file(
                    file_name, upload_path, directory, real_object_bytes)
            else:
                final_path = upload_path.replace("NEW_FILE_NAME", file_name)
                file_bytes = zip_file.open(zip_elem).read()
                self.s3_utils.save_file_in_aws(
                    file_bytes, final_path, content_type=None)
                self.result["files"].append(
                    {"file": final_path, "directory": directory})
