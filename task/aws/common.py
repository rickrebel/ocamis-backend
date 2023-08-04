import boto3
import requests
request_headers = {"Content-Type": "application/json"}


def calculate_delimiter(data):
    error_count = 0
    for row in data:
        try:
            if "|" in row:
                return "|"
        except Exception as e:
            error_count += 1
            if error_count > 3:
                print("row:\n", row)
                print("error", e)
                if "|" in row:
                    return "|"
    return ","


def obtain_decode(sample):
    sample_count = 0
    for row in sample:
        sample_count += 1
        if sample_count > 51:
            return 'str'
        is_byte = isinstance(row, bytes)
        posible_latin = False
        if is_byte:
            try:
                row.decode("utf-8")
            except Exception:
                posible_latin = True
            if posible_latin:
                try:
                    row.decode("latin-1")
                    return "latin-1"
                except Exception as e:
                    print(e)
                    return "unknown"
        else:
            return "str"
    return "utf-8"


def decode_content(data_rows, decode):
    decoded_data = []
    for row in data_rows:
        content = str(row) if decode == 'str' else row.decode(decode)
        decoded_data.append(content)
    return decoded_data


def send_simple_response(errors, event, context):
    import json
    result_data = {
        "result": {
            "errors": errors,
            "success": bool(not errors)
        },
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


def calculate_delivered_final(all_delivered, all_write=None):
    error = None
    if all_write:
        if len(all_write) > 1:
            error = f"Hay más de una clasificación de surtimiento;" \
                    f" {list(all_write)}"

    if len(all_delivered) == 1:
        return all_delivered.pop(), error
    if "partial" in all_delivered:
        return "partial", error
    has_complete = "complete" in all_delivered
    has_over = "over_delivered" in all_delivered
    has_denied = "denied" in all_delivered
    has_cancelled = "cancelled" in all_delivered
    if (has_complete or has_over) and (has_denied or has_cancelled):
        return "partial", error
    initial_list = all_delivered.copy()
    if "zero" in all_delivered:
        all_delivered.remove("zero")
    if has_over and has_complete:
        all_delivered.remove("complete")
    if has_denied and has_cancelled:
        all_delivered.remove("denied")
    if len(all_delivered) == 1:
        return all_delivered.pop(), error
    return "unknown", f"No se puede determinar el status de entrega; " \
                      f"{list(initial_list)}"


def create_connection(db_config):
    import psycopg2
    connection = psycopg2.connect(
        database=db_config.get("NAME"),
        user=db_config.get("USER"),
        password=db_config.get("PASSWORD"),
        host=db_config.get("HOST"),
        port=db_config.get("PORT"))
    return connection


class BotoUtils:

    def __init__(self, s3):
        self.s3 = s3
        aws_access_key_id = self.s3["aws_access_key_id"]
        aws_secret_access_key = self.s3["aws_secret_access_key"]
        self.s3_client = boto3.client(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        self.dev_resource = boto3.resource(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

    def get_object_file(self, file, file_type="csv"):
        import csv
        import io

        bucket_name = self.s3["bucket_name"]
        aws_location = self.s3["aws_location"]

        content_object = self.dev_resource.Object(
            bucket_name=bucket_name,
            key=f"{aws_location}/{file}"
        )
        streaming_body_1 = content_object.get()['Body']
        if file_type == "gz":
            return streaming_body_1

        object_final = streaming_body_1.read()
        # if file_type == "json":
        # if file.endswith(".csv") or file_type == "csv"
        if file_type == "csv":

            # object_final = io.BytesIO(streaming_body_1.read())
            object_final = object_final.decode("utf-8")
            csv_content = csv.reader(io.StringIO(object_final), delimiter='|')
            return csv_content
        else:
            return io.BytesIO(object_final)

    def get_csv_lines(self, file, file_type="csv"):
        import io

        bucket_name = self.s3["bucket_name"]
        aws_location = self.s3["aws_location"]

        content_object = self.dev_resource.Object(
            bucket_name=bucket_name,
            key=f"{aws_location}/{file}"
        )
        streaming_body_1 = content_object.get()['Body']
        object_final = io.BytesIO(streaming_body_1.read())
        return object_final
        # if file_type == "json":
        # if file.endswith(".csv") or file_type == "csv"

    def get_json_file(self, file_name):
        import json
        bucket_name = self.s3["bucket_name"]
        aws_location = self.s3["aws_location"]

        obj = self.s3_client.get_object(
            Bucket=bucket_name,
            Key=f"{aws_location}/{file_name}")

        return json.loads(obj['Body'].read().decode('utf-8'))

    def save_file_in_aws(self, body, final_name):
        bucket_name = self.s3.get("bucket_name")
        aws_location = self.s3.get("aws_location")

        self.s3_client.put_object(
            Body=body,
            Bucket=bucket_name,
            Key=f"{aws_location}/{final_name}",
            ContentType="text/csv",
            ACL="public-read",
        )
