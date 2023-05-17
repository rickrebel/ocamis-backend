import requests
import json
import boto3
import csv
import io
from task.aws.common import request_headers


def get_object_file(s3, file):

    aws_access_key_id = s3["aws_access_key_id"]
    aws_secret_access_key = s3["aws_secret_access_key"]
    bucket_name = s3["bucket_name"]
    aws_location = s3["aws_location"]

    dev_resource = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    content_object = dev_resource.Object(
        bucket_name=bucket_name,
        key=f"{aws_location}/{file}"
    )

    # return content_object
    streaming_body_1 = content_object.get()['Body']
    object_final = streaming_body_1.read().decode("utf-8")
    csv_content = csv.reader(io.StringIO(object_final))
    # data_rows = object_final.readlines()
    # data = object_final.read().decode("utf-8")
    return csv_content


# def analice_duplicates(event, context):
def lambda_handler(event, context):
    import psycopg2
    print("model_name", event.get("model_name"))

    iso_week = event.get("iso_week")
    year = event.get("year")

    s3 = event["s3"]
    print("HOLA DECOMPRESS")

    table_files = event["table_files"]
    # sheet_id,
    # uuid_folio,
    # folio_ocamis,
    # month

    for table_file in table_files:
        file = table_file["file"]
        csv_content = get_object_file(s3, file)
        # csv_data = csv.reader(io.StringIO(data), delimiter='|')
        headers = []
        position_delivered = None
        for idx, row in enumerate(csv_content):
            cols = row.split("|")
            if not idx:
                headers = cols
                if table_file.model == 'prescription':
                    position_delivered = headers.index("delivered_final")




    errors = []

    final_result = {
        "iso_week": iso_week,
        "year": year,
    }
    print("HOLA")
    final_result["errors"] = errors

    final_result["success"] = bool(not errors)
    result_data = {
        "result": final_result,
        "request_id": context.aws_request_id
    }
    json_result = json.dumps(result_data)
    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(webhook_url, data=json_result, headers=request_headers)
    return {
        'statusCode': 200,
        'body': json_result
    }

# data_files/nacional/issste/202107/medicament_3772_default_lap0.csv
# nacional/issste/202107/reporte_recetas_primer_nivel_202105_3.csv
