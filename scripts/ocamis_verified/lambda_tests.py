from django.conf import settings
from io import BytesIO
import os
import re
import zipfile
from lambda_aws import start_session_lambda, upload_to_s3, random_string


def create_zip_file(function_name, packages, function_text=None):
    # Create a temporary directory
    base_dir = settings.BASE_DIR
    current_string = random_string(6)
    temp_dir = f"{base_dir}/fixture/packages/{current_string}"
    # Install the packages
    for package in packages:
        os.system(f"pip3 install {package} -t {temp_dir}")
    new_root = "python"
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as zip_ref:
            if function_text:
                zip_ref.writestr(f'{function_name}.py', function_text)
            for root, dirs, files in os.walk(temp_dir):
                match = re.search(r"packages/[a-zA-Z]{6}/(.*)", root)
                # match = re.search(r'packages/(.*)', root)
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


def definitive_function_real_prev():
    base_dir = settings.BASE_DIR
    file_path = os.path.join(base_dir, "scripts/count_excel_rows.py")
    print(file_path)
    function_file = open(file_path, "r")
    current_function = "simple_function_4"
    new_zip = create_zip_file(current_function, ['boto3'], function_file.read())
    response, my_path = upload_to_s3(new_zip, current_function)
    create_lambda_function(current_function, my_path)

