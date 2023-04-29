from common import calculate_delimiter, obtain_decode, decode_content
import json
import requests


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

    message_response = {}
    if not decode:
        decode = obtain_decode(data_rows)
        if decode == "unknown":
            errors.append("No se pudo decodificar el archivo")
            message_response["errors"] = errors

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
        message_response = {
            "result": {
                "new_sheets": validated_data,
                "all_sheet_names": ["default"],
                # "delimiter": delimiter,
                "decode": decode,
            },
            "request_id": context.aws_request_id,
        }
    message_dumb = json.dumps(message_response)

    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        response_status = requests.post(webhook_url, data=message_dumb,
                                        headers={ "Content-Type": "application/json" })
    return {
        'statusCode': 200,
        'body': message_dumb
    }
