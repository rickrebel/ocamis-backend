import json


def execute_in_lambda(function_name, params, in_lambda=True):
    from scripts.common import start_session
    s3_client, dev_resource = start_session("lambda")
    if in_lambda:
        dumb_params = json.dumps(params)
        print("EJECUTADO EN LAMBDA")
        function_name = f"{function_name}:normal"
        response = s3_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=dumb_params
        )
        #print("response", response)
        #print("response['Payload']", response['Payload'])
        return json.loads(response['Payload'].read())
    else:
        print("EJECUTADO EN LOCAL")
        return globals()[function_name](params, None)


def count_excel_rows(params):
    from scripts.common import start_session
    s3_client, dev_resource = start_session("lambda")
    response = s3_client.invoke(
        FunctionName='simple_function_3:1',
        InvocationType='RequestResponse',
        Payload=json.dumps(params)
    )
    return json.loads(response['Payload'].read())


def create_file_lmd(file_bytes, upload_path, only_name, s3_vars):
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


#def lambda_handler(event, context):
def decompress_zip_aws(event, context):
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
        zip_file = zipfile.ZipFile(object_final)
    elif '.rar' in suffixes:
        zip_file = rarfile.RarFile(object_final)
    else:
        return {"files": [], "errors": ["No se reconoce el formato del archivo"]}
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


def clean_na(row):
    cols = row.tolist()
    return [col.strip() if isinstance(col, str) else "" for col in cols]


#def lambda_handler(event, context):
def explore_data_xls(event, context):
    import pandas as pd
    final_path = event["final_path"]
    nrows = event["nrows"]
    excel_file = pd.ExcelFile(final_path)
    sheets = event["sheets"]
    all_sheets = {}
    #object_excel = io.BytesIO(streaming_body_1.read())
    for sheet_name in sheets:
        data_excel = excel_file.parse(
            sheet_name,
            dtype='string', na_filter=False,
            keep_default_na=False, header=None)
        total_rows = data_excel.shape[0]
        if nrows:
            data_excel = data_excel.head(nrows)
        iter_data = data_excel.apply(clean_na, axis=1)
        list_val = iter_data.tolist()
        all_sheets[sheet_name] = {
            "all_data": list_val,
            "total_rows": total_rows,
        }
    return all_sheets
