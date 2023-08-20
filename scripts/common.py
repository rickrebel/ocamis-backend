from django.conf import settings
from io import BytesIO
import functools

bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
aws_location = getattr(settings, "AWS_LOCATION")


def similar(a, b):
    from difflib import SequenceMatcher
    if a and b:
        return SequenceMatcher(None, a, b).ratio()
    else:
        return 0


# @functools.lru_cache(maxsize=None)
def get_excel_file(file_path):
    import pandas as pd
    return pd.ExcelFile(file_path)


# esta función evalúa si hay algún parámetro en el url para el
# redireccionamiento, si no lo hay evalúa si la página de origen es distinta
# a alguna de login o register, para redirigirla al home si es el caso

def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


def read_data_dict_CSV(filename, delimiter=',', quotechar='"'):
    import csv
    dictReader = csv.DictReader(open(filename, 'rb'),
                                delimiter=delimiter, quotechar=quotechar)

    datos = []

    for row in dictReader:
        datos.append(row)

    return datos


def get_datetime_mx(datetime_utc):
    import pytz
    cdmx_tz = pytz.timezone("America/Mexico_City")
    return datetime_utc.astimezone(cdmx_tz)


def build_s3():
    return {
        "aws_access_key_id": getattr(settings, "AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": getattr(settings, "AWS_SECRET_ACCESS_KEY"),
        "bucket_name": getattr(settings, "AWS_STORAGE_BUCKET_NAME"),
        "region_aws": getattr(settings, "AWS_S3_REGION_NAME"),
        "aws_location": getattr(settings, "AWS_LOCATION"),
    }


def start_session(service='s3', endpoint_url=None):
    import boto3
    from botocore.config import Config
    is_prod = getattr(settings, "IS_PRODUCTION", False)
    if not is_prod:
        return None, None
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    region_aws = getattr(settings, "AWS_S3_REGION_NAME")
    if endpoint_url is None:
        config = Config(read_timeout=600, retries={'max_attempts': 0})
    else:
        config = Config(
            read_timeout=600,
            retries={ 'max_attempts': 0 },
            s3={"use_accelerate_endpoint": True, "addressing_style": "path"}
        )
    # print("endpoint_url", endpoint_url)
    s3_client = boto3.client(
        service,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_aws,
        config=config,
        # endpoint_url=endpoint_url,
    )
    if service == 's3':
        s3_resource = boto3.resource(
            service,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_aws,
        )
        return s3_client, s3_resource
    else:
        return s3_client, None


def get_file(file_obj, dev_resource=None):
    if dev_resource:
        try:
            content_object = dev_resource.Object(
                bucket_name=bucket_name,
                #key=f"{aws_location}/{file_obj.file.name}"
                key=f"{aws_location}/{file_obj.file.name}"
                )
            # RICK AWS corroborar el cambio:
            # content_object_prev = dev_resource.Object(
            #     #bucket_name, "data_files/%s" % self.file.name)
            #     bucket_name, f"{aws_location}\\{self.file.name}")
            return content_object.get()['Body']
            # RICK AWS corroborar el cambio:
            # return BytesIO(content_object.get()["Body"].read())
            #return content_object.get()['Body'].read().decode('utf-8')
        except Exception as e:
            print(e)
            return {"errors": [f"Error leyendo los datos: {e}"]}
    else:
        return file_obj.final_path


def get_csv_file(file_obj, s3_client=None):
    import pandas as pd
    if s3_client:
        try:
            content_object = s3_client.get_object(
                Bucket=bucket_name,
                Key=f"{aws_location}/{file_obj.file.name}")
            # print(BytesIO(content_object['Body'].read()))
            csv_file = BytesIO(content_object['Body'].read())
            return pd.read_csv(csv_file, on_bad_lines='skip')
            #return pd.read_csv(BytesIO(content_object['Body'].read()))
        except Exception as e:
            print(e)
            return {"errors": [f"Error leyendo los datos: {e}"]}
    else:
        return file_obj.final_path


def create_file(file_bytes, s3_client=None, file_obj=None, only_name=None, final_path=None):
    from inai.models import set_upload_path
    from django.core.files import File
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    all_errors = []
    final_file = None
    try:
        if s3_client:
            if not final_path:
                final_path = set_upload_path(file_obj, only_name)
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
        else:
            final_file = File(BytesIO(file_bytes), name=only_name)
    except Exception as e:
        print(e)
        all_errors += ["Error leyendo los datos %s" % e]
    return final_file, all_errors


def create_file_big(file_obj, zip_content, only_name, s3_client=None):
    from inai.models import set_upload_path
    from django.core.files import File
    all_errors = []
    final_file = None
    final_bucket_name = bucket_name
    # final_bucket_name = 'cdn-desabasto.s3-accelerate'
    # final_bucket_name = 'cdn-desabasto.s3-accelerate.amazonaws.com'

    try:
        final_path = set_upload_path(file_obj, only_name)
        print("COMIENZA EL MULTIPART")
        multipart_upload = s3_client.create_multipart_upload(
            Bucket=final_bucket_name,
            Key=f"{aws_location}/{final_path}",
            ACL='public-read',
        )
        print("multipart_upload", multipart_upload)
        upload_id = multipart_upload['UploadId']
        # space
        print("comenzamos")
        part_number = 1
        parts = []
        while True:
            data = zip_content.read(1024 * 1024 * 50)
            # data = zip_content.read(1024 * 10)
            if not data:
                break
            part_number += 1
            response = s3_client.upload_part(
                Bucket=final_bucket_name,
                Key=f"{aws_location}/{final_path}",
                Body=data,
                PartNumber=part_number,
                UploadId=upload_id,
            )
            print("response", response)
            parts.append({
                'PartNumber': part_number,
                'ETag': response['ETag'],
            })
        success_file = s3_client.complete_multipart_upload(
            Bucket=final_bucket_name,
            Key=f"{aws_location}/{final_path}",
            UploadId=upload_id,
            MultipartUpload={'Parts': parts},
        )
        print("success_file", success_file)
        if success_file:
            final_file = final_path
        else:
            all_errors += [f"No se pudo insertar el archivo {final_path}"]
    except Exception as e:
        print(e)
        all_errors += ["Error leyendo los datos %s" % e]
    return final_file, all_errors


def using_example_big():
    from inai.models import Petition
    local_file = 'D:\\info_330018023000822.zip'
    petition = Petition.objects.get(folio_petition='330018023000822')
    endpoint = "cdn-desabasto.s3-accelerate.amazonaws.com"
    s3_client, s3_resource = start_session('s3', endpoint)
    with open(local_file, 'rb') as file_obj:
        create_file_big(
            petition, file_obj, 'info_330018023000822.zip', s3_client)
    # upload_s3_files = upload_s3_files(
    #     'D:\\RecetasIMSS\\req_mayo_2020_02.txt.gz', 'nacional/imss/202107/')


# using_example_big()


def explore_sheets(file_control):
    from data_param.models import Transformation
    file_transformations = Transformation.objects.filter(
        file_control=file_control,
        clean_function__name__icontains="_tabs_").prefetch_related(
        "clean_function")
    include_names = exclude_names = include_idx = exclude_idx = None

    for transform in file_transformations:
        current_values = transform.addl_params["value"].split(",")
        func_name = transform.clean_function.name
        all_names = [name.upper().strip() for name in current_values]
        if func_name == 'include_tabs_by_name':
            include_names = all_names
        elif func_name == 'exclude_tabs_by_name':
            exclude_names = all_names
        elif func_name == 'include_tabs_by_index':
            include_idx = [int(val.strip()) for val in current_values]
        elif func_name == 'exclude_tabs_by_index':
            exclude_idx = [int(val.strip()) for val in current_values]

    return include_names, exclude_names, include_idx, exclude_idx


"""
python ./manage.py dumpdata --exclude auth --exclude contenttypes --exclude authtoken --exclude admin.LogEntry --exclude sessions --indent 2 -v 2  > fixture/todo_desabasto.json 
"""
