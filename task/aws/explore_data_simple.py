# from common import calculate_delimiter, obtain_decode, decode_content, send_simple_response
from task.aws.common import (
    calculate_delimiter, obtain_decode, decode_content, send_simple_response)


def divide_rows(data_rows, delimiter):
    # print("DIVIDE_ROWS", data_rows)
    structured_data = []
    for row_seq, row in enumerate(data_rows, 1):
        # print("\n")
        row_data = row.split(delimiter)
        structured_data.append(row_data)
    return structured_data


def calculate_delimiter_own(data):
    if "|" not in data[:3000]:
        return ","
    else:
        return "|"


# def explore_data_xls(event, context):
def lambda_handler(event, context):
    import boto3
    import io

    errors = []
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
    streaming_body_1 = content_object.get()['Body']
    object_final = io.BytesIO(streaming_body_1.read())

    data_rows = object_final.readlines()
    # print("INICIO", data_rows)
    total_rows = len(data_rows)
    data_rows = data_rows[:220]
    # print("FINAL", data_rows)
    decode = event.get("decode")
    delimiter = event.get("delimiter")

    result = {}
    if not decode:
        decode = obtain_decode(data_rows)
        if decode == "unknown":
            errors.append("No se pudo decodificar el archivo")

    if not errors:

        all_rows = decode_content(data_rows, decode)
        if not delimiter:
            delimiter = calculate_delimiter(data_rows)
        validated_data_default = divide_rows(all_rows, delimiter)
        validated_data = {
            "default": {
                "all_data": validated_data_default[:200],
                "total_rows": total_rows,
            }
        }
        result["new_sheets"] = validated_data
        result["all_sheet_names"] = ["default"]
        result["decode"] = decode
    return send_simple_response(event, context, errors, result)
