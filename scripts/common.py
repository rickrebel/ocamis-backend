# encoding:utf-8

from django.conf import settings
bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
aws_location = getattr(settings, "AWS_LOCATION")
from io import BytesIO

def similar(a, b):
    from difflib import SequenceMatcher
    if a and b:
        return SequenceMatcher(None, a, b).ratio()
    else:
        return 0

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



def start_session():
    import boto3
    is_prod = getattr(settings, "IS_PRODUCTION", False)
    if not is_prod:
        return None, None
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    #s3 = boto3.resource(
    s3_client = boto3.client(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    dev_resource = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    return s3_client, dev_resource


def get_file(file_obj, dev_resource=None):

    if dev_resource:
        try:
            content_object = dev_resource.Object(
                bucket_name=bucket_name,
                #key=f"{aws_location}/{file_obj.file.name}"
                key=f"{aws_location}/{file_obj.file.name}"
                )
            # RICK AWS corroborar el cambio:
            """
            content_object_prev = dev_resource.Object(
                #bucket_name, "data_files/%s" % self.file.name)
                bucket_name, f"{aws_location}\\{self.file.name}")
            """
            return content_object.get()['Body']
            # RICK AWS corroborar el cambio:
            # return BytesIO(content_object.get()["Body"].read())
            #return content_object.get()['Body'].read().decode('utf-8')
        except Exception as e:
            print(e)
            return {"errors": [f"Error leyendo los datos: {e}"]}
    else:
        return file_obj.final_path


def create_file(file_obj, file_bytes, only_name, s3_client=None):
    from inai.models import set_upload_path
    from django.core.files import File
    all_errors = []
    final_file = None
    try:
        if s3_client:
            final_path = set_upload_path(file_obj, only_name)
            success_file = s3_client.put_object(
                Key=f"{aws_location}/{final_path}",
                Body=file_bytes,
                Bucket=bucket_name,
                ACL='public-read',
                #ContentType='application/pdf'
            )
            if success_file:
                final_file = final_path
            else:
                all_errors += [f"No se pudo insertar el archivo {final_path}"]
        else:
            final_file = File(BytesIO(file_bytes), name=only_name)
    except Exception as e:
        print(e)
        all_errors += [u"Error leyendo los datos %s" % e]
    return final_file, all_errors




"""

python ./manage.py dumpdata --exclude auth --exclude contenttypes --exclude authtoken --exclude admin.LogEntry --exclude sessions --indent 2 -v 2  > fixture/todo_desabasto.json 

"""