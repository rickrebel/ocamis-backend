
def lambda_handler_old(event, context):
    import pandas as pd
    import boto3
    import io
    aws_access_key_id = event["s3"]["aws_access_key_id"]
    aws_secret_access_key = event["s3"]["aws_secret_access_key"]
    bucket_name = event["s3"]["bucket_name"]
    aws_location = event["s3"]["aws_location"]
    #s3_client = boto3.client(
    #    's3', aws_access_key_id=aws_access_key_id,
    #    aws_secret_access_key=aws_secret_access_key)
    dev_resource = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    file = event["file"]
    #object_from_client = s3_client.get_object(
    #    Bucket=bucket_name,
    #    Key=f"{aws_location}/{file}"
    #)
    content_object = dev_resource.Object(
        bucket_name=bucket_name,
        # key=f"{aws_location}/{file_obj.file.name}"
        key=f"{aws_location}/{file}"
    )
    #print(content_object)
    #final_file = content_object.get()['Body']
    streaming_body_1 = content_object.get()['Body']
    #print(final_file)
    #final_file.seek(0)
    #streaming_body_1 = object_from_client['Body']
    #print("object_from_client", object_from_client)
    print("streaming_body_1", streaming_body_1)
    sheets = event["sheets"]
    result = {}
    object_excel = io.BytesIO(streaming_body_1.read())
    for sheet_name in sheets:
        #excel_file = pd.read_excel(final_file, sheet_name=sheet_name)
        #excel_file = pd.read_excel(content_object["body"], sheet_name=sheet_name)
        #excel_file = pd.read_excel(object_from_client["body"], sheet_name=sheet_name)
        excel_file = pd.read_excel(object_excel, sheet_name=sheet_name)
        current_count = excel_file.shape[0]
        result[sheet_name] = current_count
    return result


def lambda_handler(event, context):
    import pandas as pd
    import boto3
    import io
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
    sheets = event["sheets"]
    result = {}
    object_excel = io.BytesIO(streaming_body_1.read())
    for sheet_name in sheets:
        excel_file = pd.read_excel(object_excel, sheet_name=sheet_name)
        current_count = excel_file.shape[0]
        result[sheet_name] = current_count
    return result
