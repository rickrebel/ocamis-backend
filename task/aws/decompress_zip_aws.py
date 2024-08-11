from task.aws.common import BotoUtils, send_simple_response_2
import zipfile
import rarfile
import os
unrar_tool = os.environ.get("UNRAR_TOOL", None)
if unrar_tool:
    rarfile.UNRAR_TOOL = '/opt/bin/unrar2'
# get enviroment variable AWS_LOCATION


# def decompress_zip_aws(event, context):
def lambda_handler(event, context):

    decompress_zip = Decompress(event, context)
    suffixes = event.get("suffixes")
    upload_path = event.get("upload_path")
    decompress_zip.decompress(suffixes, upload_path)
    # return send_simple_response(event, context, errors, result)
    decompress_zip.result["errors"] = decompress_zip.errors + \
        decompress_zip.s3_utils.errors
    return send_simple_response_2(event, context, decompress_zip.result)


class Decompress:

    def __init__(self, event: dict, context):
        self.context = context
        self.result = {"files": [], "errors": []}
        self.errors = []
        # self.s3_utils = BotoUtils(event["s3"])
        self.s3_utils = BotoUtils(event.get("s3"))
        file = event["file"]
        self.object_bytes = self.s3_utils.get_object_file(file, "zip")

    def decompress(
            self, suffixes, upload_path, prev_directory="", object_bytes=None):
        from io import BytesIO
        if not object_bytes:
            object_bytes = self.object_bytes
        if '.zip' in suffixes:
            zip_file = zipfile.ZipFile(object_bytes)
        elif '.rar' in suffixes:
            try:
                zip_file = rarfile.RarFile(object_bytes)
            except rarfile.NotRarFile:
                error = f"No se reconoce el formato del archivo, path: {upload_path}"
                self.errors.append(error)
                return
        else:
            self.errors.append("No se reconoce el formato del archivo")
            return

        for zip_elem in zip_file.infolist():
            if zip_elem.is_dir():
                continue
            file_name = zip_elem.filename
            if "desktop.ini" in file_name:
                continue
            if "Thumbs.db" in file_name:
                continue
            # print("----------------------")
            # print("file_name", file_name)
            directory = ""
            only_name = file_name
            if "/" in file_name:
                pos_slash = file_name.rfind("/")
                only_name = file_name[pos_slash + 1:]
                directory = file_name[:pos_slash]
            # print(f"new_directory -->{directory}<--")
            if prev_directory and directory:
                # print("prev_directory", prev_directory)
                prev_directory = f"{prev_directory}/"
            directory = f"{prev_directory}{directory}"

            if directory:
                folders = directory.split("/")
                final_directory = []
                for folder in folders:
                    if folder not in final_directory:
                        final_directory.append(folder)
                directory = "/".join(final_directory)
                file_name = f"{directory}/{only_name}"
                file_name = file_name.replace("//", "/")

            # evaluate if file_name is a .zip or .rar file
            if only_name.endswith(".zip") or only_name.endswith(".rar"):
                object_bytes = zip_file.open(zip_elem).read()
                real_object_bytes = BytesIO(object_bytes)
                directory += f"/{only_name.replace('.', '_')}"
                # print("zip or rar file")
                # print("file_name", file_name)
                # print("directory", directory)
                self.decompress(
                    file_name, upload_path, directory, real_object_bytes)
            else:
                final_path = upload_path.replace("NEW_FILE_NAME", file_name)
                file_bytes = zip_file.open(zip_elem).read()
                self.s3_utils.save_file_in_aws(
                    file_bytes, final_path, content_type=None)
                # print("final_path", final_path)
                # print("directory", directory)
                self.result["files"].append(
                    {"file": final_path, "directory": directory})
