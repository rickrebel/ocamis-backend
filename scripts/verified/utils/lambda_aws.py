import zipfile
import os
import boto3
from io import BytesIO
import re
from django.conf import settings


def start_session_lambda():
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    return boto3.client(
        'lambda', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=getattr(settings, "AWS_S3_REGION_NAME")
    )


def random_string(length=6):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters, k=length))


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


def create_zip_files(function_name, function_files):
    # Create a temporary directory
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as zip_ref:
            for file in function_files:
                function_text = file.read()
                zip_ref.writestr(f'{function_name}.py', function_text)
        zip_bytes.seek(0)
        return zip_bytes.read()


def create_zip_packages(packages, python_version=3.9):
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


def create_lambda_function(function_name, final_path, python_version=3.10):
    aws_location = getattr(settings, "AWS_LOCATION")
    s3_key = f"{aws_location}/{final_path}"
    s3_bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    lambda_client = start_session_lambda()
    response_get = lambda_client.get_function(
        FunctionName=function_name)
    if not response_get.get("FunctionArn"):
        response_create = lambda_client.create_function(
            FunctionName=function_name,
            Runtime=f'python{python_version}',
            Role="arn:aws:iam::032892915740:role/full_lambda",
            Handler=f"{function_name}.lambda_handler",
            Code={
                'S3Bucket': s3_bucket,
                'S3Key': s3_key
            },
        )
        return response_create
    else:
        response_update = lambda_client.update_function_code(
            FunctionName=function_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key,
            Publish=True,

        )
        return response_update


def definitive_function_real(function_name, layers, python_version=3.10):
    if not layers:
        layers = []
    base_dir = settings.BASE_DIR
    function_files = []
    for file_name in [function_name, "common"]:
        file_path = os.path.join(base_dir, f"task/aws/{file_name}.py")
        function_files.append(open(file_path, "r"))
    new_zip = create_zip_files(function_name, function_files)
    response, my_path = upload_to_s3(new_zip, function_name)
    create_lambda_function(function_name, my_path, python_version)


def create_lambda_layer(layer_name, final_path, python_version):
    lambda_client = start_session_lambda()
    aws_location = getattr(settings, "AWS_LOCATION")
    s3_key = f"{aws_location}/{final_path}"
    response = lambda_client.publish_layer_version(
        LayerName=layer_name,
        Content={
            'S3Bucket': getattr(settings, "AWS_STORAGE_BUCKET_NAME"),
            'S3Key': s3_key
        },
        CompatibleRuntimes=[f'python{python_version}'],
        CompatibleArchitectures=['x86_64']
    )
    return response


def build_lambda_layer(
        layer_name="my_layer1", packages=[], python_version="3.10"):
    zip_layer = create_zip_packages(packages)
    resp, layer_path = upload_to_s3(zip_layer, layer_name)
    create_lambda_layer(layer_name, layer_path, python_version)


# from scripts.verified.lambda import build_lambda_layer
# definitive_function_real()
# build_lambda_layer("pandas_with_complements",
#                   ["XlsxWriter", "xlrd", "lxml", "wheel", "pandas",
#                    "numpy", "pyxlsb"])
#
# build_lambda_layer("pandas_complements",
#                   ["XlsxWriter", "xlrd", "lxml", "wheel", "pyxlsb"])
# build_lambda_layer("other_complements_psycopg2_and_unidecode_10",
#                   ["psycopg2", "unidecode"])
# build_lambda_layer("csv_complements", ["csv", "uuid"])
# build_lambda_layer("request_package", ["requests"])
# build_lambda_layer("psycopg2-binary", ["psycopg2-binary"])
# build_lambda_layer("gz_10", ["gz"])
