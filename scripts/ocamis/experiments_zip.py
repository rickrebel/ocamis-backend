
def zip_experiments():
    import zipfile
    import datetime
    url = "C:\\Users\\Ricardo\\dev\\desabasto\\desabasto-api\\fixture\\zipfolder.zip"

    #directory = self.file.url
    directory = url
    #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
    #zip_file = zipfile.ZipFile(self.file.url)
    zip_file = zipfile.ZipFile(url)
    all_files = zip_file.namelist()
    print(all_files)
    for curr_file in all_files:
        print(curr_file)

    with zipfile.ZipFile(url, mode="r") as archive:
        for info in archive.infolist():
            print(f"Es directorio: {info.is_dir()}")
            print(f"Filename: {info.filename}")
            print(f"Modified: {datetime.datetime(*info.date_time)}")
            print(f"Normal size: {info.file_size} bytes")
            print(f"Compressed size: {info.compress_size} bytes")
            print("-" * 20)
        archive.close()

    #with zipfile.ZipFile(self.url, 'r') as zip_ref:
    with zipfile.ZipFile(url, 'r') as zip_ref:
        zip_ref.extractall(directory)               
    #ZipFile.extractall(path=None, members=None, pwd=None)   
    #for f in os.listdir(directory):
    for f in all_files:
        new_file = self
        new_file.pk = None
        new_file = DataFile.objects.create(
            file="%s%s" % (directory, f),
            origin_file=self,
            date=self.date,
            status=initial_status,
            #Revisar si lo más fácil es poner o no los siguientes:
            file_control=file_control,
            petition=self.petition,
            petition_month=file.petition_month,
            )
    self = new_file
    suffixes.remove('.zip')


def create_file_lmd(file_bytes, upload_path, only_name, s3_vars):
    from inai.models import set_upload_path
    from django.core.files import File
    all_errors = []
    final_file = None
    aws_location = s3_vars["aws_location"]
    bucket_name = s3_vars["bucket_name"]
    s3_client = s3_vars["s3_client"]
    try:
        final_path = upload_path.replace("NEW_FILE_NAME", only_name)
        success_file = s3_client.put_object(
            Key=f"{aws_location}/{final_path}",
            Body=file_bytes,
            Bucket=bucket_name,
            ACL='public-read',
        )
        if success_file:
            final_file = final_path
        else:
            all_errors += [f"No se pudo insertar el archivo {final_path}"]
    except Exception as e:
        print(e)
        all_errors += [u"Error leyendo los datos %s" % e]
    return final_file, all_errors


def lambda_handler(event, context):
    import boto3
    import io
    import zipfile
    import rarfile
    aws_access_key_id = event["s3"]["aws_access_key_id"]
    aws_secret_access_key = event["s3"]["aws_secret_access_key"]
    bucket_name = event["s3"]["bucket_name"]
    aws_location = event["s3"]["aws_location"]

    dev_resource = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    file = event["file"]
    content_object = dev_resource.Object(
        bucket_name=bucket_name,
        key=f"{aws_location}/{file}"
    )
    s3_client = boto3.client(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    streaming_body_1 = content_object.get()['Body']
    object_final = io.BytesIO(streaming_body_1.read())
    suffixes = event["suffixes"]
    upload_path = event["upload_path"]
    if '.zip' in suffixes:
        zip_file = zipfile.ZipFile(buffer)
    elif '.rar' in suffixes:
        zip_file = rarfile.RarFile(buffer)
    all_new_files = []
    all_errors = []
    for zip_elem in zip_file.infolist():
        if zip_elem.is_dir():
            continue
        pos_slash = zip_elem.filename.rfind("/")
        only_name = zip_elem.filename[pos_slash + 1:]
        directory = (zip_elem.filename[:pos_slash]
                     if pos_slash > 0 else None)
        file_bytes = zip_file.open(zip_elem).read()
        s3_vars = event["s3"]
        s3_vars["s3_client"] = s3_client
        curr_file, file_errors = create_file_lmd(
            file_bytes, upload_path, only_name, s3_vars)
        if file_errors:
            all_errors += file_errors
            continue
        all_new_files.append({"file": curr_file, "directory": directory})

    return {"files": all_new_files, "errors": all_errors}
