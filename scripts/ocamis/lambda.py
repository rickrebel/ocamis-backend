import zipfile
import tempfile
import shutil
import os
import boto3
from io import BytesIO
import re
from django.conf import settings


def random_string(len=6):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters, k=len))


def create_zip_file(function_name, packages, function_text=None):
    # Create a temporary directory
    base_dir = settings.BASE_DIR
    temp_dir_prev = tempfile.mkdtemp()
    temp_dir = f"{base_dir}/fixture/packages/{random_string(6)}"
    # Install the packages
    for package in packages:
        os.system(f"pip3 install {package} -t {temp_dir}")
    #new_root = "python"
    new_root = "python"
    # Create the zip file
    #zip_file2 = f'{function_name}.zip'
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as zip_ref:
            if function_text:
                zip_ref.writestr(f'{function_name}.py', function_text)
            for root, dirs, files in os.walk(temp_dir):
                match = re.search(r'packages/(.*)', root)
                if match:
                    current_root = match.group(1)
                else:
                    current_root = ""
                for file in files:
                    print(os.path.join(new_root, current_root, file))
                    zip_ref.write(os.path.join(root, file), os.path.join(new_root, current_root, file))
        # Reset the BytesIO object's position to the beginning
        zip_bytes.seek(0)
        return zip_bytes.read()



def upload_to_s3(zip_file, function_name):
    from scripts.common import start_session
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    final_path = f"experiment/{function_name}.zip"
    s3_client, dev_resource = start_session()
    success_file = s3_client.put_object(
        Key=f"{aws_location}/{final_path}",
        Body=zip_file,
        Bucket=bucket_name,
        #ACL='public-read',
    )
    return success_file, final_path


def start_session_lambda():
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    return boto3.client(
        'lambda', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=getattr(settings, "AWS_S3_REGION_NAME")
    )


def create_lambda_function(function_name, final_path):
    aws_location = getattr(settings, "AWS_LOCATION")
    s3_key = f"{aws_location}/{final_path}"
    lambda_client = start_session_lambda()
    response_create = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.9',
        Role="arn:aws:iam::032892915740:role/full_lambda",
        Handler=f"{function_name}.lambda_handler",
        Code={
            #'ZipFile': zip_file,
            'S3Bucket': getattr(settings, "AWS_STORAGE_BUCKET_NAME"),
            'S3Key': s3_key
        },
    )
    return response_create

function_text_simple = '''
#import numpy as np

def lambda_handler(event, context):
    list_of_integers = event["list_of_integers"]
    total_count = 0
    for elem in list_of_integers:
        total_count += elem
    result = total_count        
    # result = np.sum(list_of_integers)
    return {"result": result}
    '''


function_text_original = '''
import numpy as np

def lambda_handler(event, context):
    list_of_integers = event["list_of_integers"]
    result = np.sum(list_of_integers)
    return {"result": result}
    '''


def definitive_function():
    current_function = "example_function20"
    new_zip = create_zip_file(current_function, ['numpy'], function_text_original)
    response, my_path = upload_to_s3(new_zip, current_function)
    create_lambda_function(current_function, my_path)


def definitive_function_real():
    base_dir = settings.BASE_DIR
    file_path = os.path.join(base_dir, "scripts/count_excel_rows.py")
    print(file_path)
    function_file = open(file_path, "r")
    current_function = "simple_function_4"
    new_zip = create_zip_file(current_function, ['boto3'], function_file.read())
    response, my_path = upload_to_s3(new_zip, current_function)
    create_lambda_function(current_function, my_path)


def create_lambda_layer(layer_name, final_path):
    lambda_client = start_session_lambda()
    aws_location = getattr(settings, "AWS_LOCATION")
    s3_key = f"{aws_location}/{final_path}"
    response = lambda_client.publish_layer_version(
        LayerName=layer_name,
        Content={
            'S3Bucket': getattr(settings, "AWS_STORAGE_BUCKET_NAME"),
            'S3Key': s3_key
        },
        CompatibleRuntimes=['python3.9'],
    )
    return response


def definitive_lambda():
    layer_name = "pandas_example_2"
    zip_layer = create_zip_file(layer_name, ['pandas'])
    resp, layer_path = upload_to_s3(zip_layer, layer_name)
    create_lambda_layer(layer_name, layer_path)


#definitive_function()
definitive_function_real()
#definitive_lambda()


