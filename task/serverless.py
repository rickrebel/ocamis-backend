import json
from django.conf import settings
from task.aws.start_build_csv_data import lambda_handler as start_build_csv_data
from task.aws.start_build_csv_data import lambda_handler as prepare_files
from task.aws.save_csv_in_db import lambda_handler as save_csv_in_db
from task.aws.xls_to_csv import lambda_handler as xls_to_csv


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def execute_in_lambda(function_name, params, in_lambda=True):
    from scripts.common import start_session
    s3_client, dev_resource = start_session("lambda")
    if in_lambda:
        dumb_params = json.dumps(params)
        print("SE ENVÍA A LAMBDA", function_name)
        function_name = f"{function_name}:normal"
        response = s3_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=dumb_params
        )
        print("response", response)
        #print("response['Payload']", response['Payload'])
        payload_response = json.loads(response['Payload'].read())
        if "errorMessage" in payload_response:
            print("ERROR EN LAMBDA:\n", payload_response)
            #raise Exception(payload_response["errorMessage"])
        return payload_response
    else:
        print("EJECUTADO EN LOCAL")
        context = {"aws_request_id": "local"}
        return globals()[function_name](params, context)


def execute_async(current_task, params):
    import threading
    from scripts.common import start_session
    function_name = current_task.task_function_id
    s3_client, dev_resource = start_session("lambda")
    use_local_lambda = getattr(settings, "USE_LOCAL_LAMBDA", False)
    if globals().get(function_name, False) and use_local_lambda:
        print("SE EJECUTA EN LOCAL")
        request_id = current_task.id
        params["artificial_request_id"] = str(request_id)
        current_task.request_id = request_id
        current_task.status_task_id = "running"
        current_task.save()
        # payload_response = json.loads(response['Payload'].read())
        # print("payload_response", payload_response)

        def run_in_thread():
            class Context:
                def __init__(self, request_id):
                    self.aws_request_id = request_id
            globals()[function_name](params, Context(request_id))

        t = threading.Thread(target=run_in_thread)
        t.start()
        return current_task
    else:
        function_final = f"{function_name}:normal"
        dumb_params = json.dumps(params)
        try:
            response = s3_client.invoke(
                FunctionName=function_final,
                InvocationType='Event',
                LogType='Tail',
                Payload=dumb_params
            )
            # print("response", response, "\n")
            request_id = response["ResponseMetadata"]["RequestId"]
            current_task.request_id = request_id
            current_task.status_task_id = "running"
            current_task.save()
            # print("SE GUARDÓ BIEN")
            # payload_response = json.loads(response['Payload'].read())
            # print("payload_response", payload_response)
            return current_task
        except Exception as e:
            print("ERROR EN LAMBDA:\n", e)
            current_task.status_task_id = "not_sent"
            current_task.errors = [str(e)]
            current_task.save()
            return None


def async_in_lambda(function_name, params, task_params):
    from task.models import AsyncTask
    from datetime import datetime

    api_url = getattr(settings, "API_URL", False)
    params["webhook_url"] = f"{api_url}task/webhook_aws/"
    function_after = task_params.get("function_after", f"{function_name}_after")
    query_kwargs = {
        "task_function_id": function_name,
        "function_after": function_after,
        "original_request": params,
        "status_task_id": "pending",
        "date_start": datetime.now(),
    }
    for field in ["parent_task", "params_after"]:
        if field in task_params:
            query_kwargs[field] = task_params[field]

    for model in task_params["models"]:
        query_kwargs[camel_to_snake(model.__class__.__name__)] = model
    # print("query_kwargs:\n", query_kwargs, "\n")
    current_task = AsyncTask.objects.create(**query_kwargs)
    # print("SE ENVÍA A LAMBDA ASÍNCRONO", function_name)
    if function_name == "save_csv_in_db":
        pending_tasks = AsyncTask.objects.filter(
            task_function_id=function_name,
            status_task__is_completed=False)
        if pending_tasks.count():
            current_task.date_start = None
            current_task.status_task_id = "queue"
            current_task.save()
            return current_task
    else:
        return execute_async(current_task, params)


def count_excel_rows(params):
    from scripts.common import start_session
    s3_client, dev_resource = start_session("lambda")
    response = s3_client.invoke(
        FunctionName='simple_function_3:normal',
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
        all_errors += ["Error leyendo los datos %s" % e]
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
