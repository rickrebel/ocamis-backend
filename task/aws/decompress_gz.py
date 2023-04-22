import requests
import json
import boto3
import io
request_headers = {"Content-Type": "application/json"}


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

    return content_object
    # streaming_body_1 = content_object.get()['Body']
    # return streaming_body_1
    # object_final = io.BytesIO(streaming_body_1.read())
    # return object_final


def write_split_files(complete_file, simple_name, event):
    s3 = event["s3"]
    aws_access_key_id = s3["aws_access_key_id"]
    aws_secret_access_key = s3["aws_secret_access_key"]
    aws_location = s3["aws_location"]
    bucket_name = s3["bucket_name"]
    decode = event.get("decode")
    delimiter = event.get("delimiter")

    s3_client = boto3.client(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    [base_name, extension] = simple_name.rsplit(".", 1)
    file_num = 0
    last_file = None
    size_hint = 330 * 1000000
    new_files = []
    errors = []
    header_validated = []
    tail_validated = []
    while True and not errors:
        buf = complete_file.readlines(size_hint)
        if not buf:
            print("No hay más datos")
            break

        if not header_validated:
            header_data = buf[:220]
            tail_data = buf[-50:]

            if not decode:
                decode = obtain_decode(header_data)
                if decode == "unknown":
                    errors.append("No se pudo decodificar el archivo")
            sample_header = decode_content(header_data, decode)
            if not delimiter:
                delimiter = calculate_delimiter(sample_header)
            if errors:
                break

            sample_tail = decode_content(tail_data, decode)
            header_validated = divide_rows(sample_header, delimiter)
            tail_validated = divide_rows(sample_tail, delimiter)

        file_num += 1
        curr_only_name = f"{base_name}_{file_num}.{extension}"
        total_rows = len(buf)
        buf = b"".join(buf)
        print("rr_file_name", curr_only_name)
        s3_client.put_object(
            Body=buf,
            Bucket=bucket_name,
            Key=f"{aws_location}/{curr_only_name}",
            ContentType="text/csv",
            ACL="public-read",
        )
        # print("éxito en creación de archivo")
        # print("errors", errors)
        current_file = {
            "total_rows": total_rows,
            "final_path": curr_only_name,
            "sheet_name": file_num,
        }
        new_files.append(current_file)
    result = {
        "new_files": new_files,
        "decode": decode,
        "delimiter": delimiter,
        "all_data": header_validated,
        "tail_data": tail_validated,
    }

    return result, errors


# def decompress_gz(event, context):
def lambda_handler(event, context):
    import gzip

    file = event["file"]
    s3 = event["s3"]

    gz_obj = get_object_file(s3, file)
    decompressed_path = file.replace(".gz", "")
    pos_slash = decompressed_path.rfind("/")
    only_name = decompressed_path[pos_slash + 1:]

    new_files = {}
    with gzip.GzipFile(fileobj=gz_obj.get()['Body']) as gzip_file:
        result, errors = write_split_files(gzip_file, only_name, event)
    result["matched"] = True
    result["file_type_id"] = "split"

    message_response = {
        "result": result,
        "errors": errors,
        "request_id": context.aws_request_id,
    }
    message_dumb = json.dumps(message_response)

    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(
            webhook_url, data=message_dumb, headers=request_headers)
    return {
        'statusCode': 200,
        'body': message_dumb
    }


def divide_rows(data_rows, delimiter):
    # print("DIVIDE_ROWS", data_rows)
    structured_data = []
    for row_seq, row in enumerate(data_rows, 1):
        # print("\n")
        row_data = row.split(delimiter)
        row_data = [x.strip() for x in row_data]
        structured_data.append(row_data)
    return structured_data


def obtain_decode(sample):
    for row in sample:
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


def calculate_delimiter(data):
    for row in data:
        if "|" in row:
            return "|"
    return ","

