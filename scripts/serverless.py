import json


def count_excel_rows(params):
    from scripts.common import start_session
    s3_client, dev_resource = start_session("lambda")
    response = s3_client.invoke(
        FunctionName='simple_function_3',
        InvocationType='RequestResponse',
        Payload=json.dumps(params)
    )
    print("HOLA count_excel_rows")
    print("response", response)
    return json.loads(response['Payload'].read())
