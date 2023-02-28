
for obj in bucket.objects.all():
    print(obj.key)import boto3
import json

s3 = boto3.resource(
    's3', aws_access_key_id='AKIAICSGL3ROH3GVALGQ',
    aws_secret_access_key='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')
bucket = s3.Bucket('cdn-desabasto')
# Iterates through all the objects, doing the pagination for you. Each obj
# is an ObjectSummary, so it doesn't contain the body. You'll need to call
# get to get the whole body.


    key = obj.key
    body = obj.get()['Body'].read()



with io.open(path_json, "r", encoding="UTF-8") as file:
    data = json.load(file)
    file.close()


content_object = s3.Object('cdn-desabasto', 'data_files/todas.json')
file_content = content_object.get()['Body'].read().decode('utf-8')
json_content = json.loads(file_content)
data = json_content

print(json_content['Details'])

https://cdn-desabasto.s3.us-west-2.amazonaws.com/data_files/estatal/issags/202203/ASSSA000643.csv

https://cdn-desabasto.s3.us-west-2.amazonaws.com/data_files/estatal/issags/202203/ASSSA000643.csv

import io
with io.open(self.final_path, "r", encoding="UTF-8") as file_open:
    data = file_open.read()
    file_open.close()


import json
import boto3

s3 = boto3.resource(
    's3', aws_access_key_id='AKIAICSGL3ROH3GVALGQ',
    aws_secret_access_key='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')

key = 'data_files/estatal/issags/202203/ASSSA000643.csv'
content_object = s3.Object('cdn-desabasto', key)
file_content = content_object.get()['Body'].read().decode('utf-8')


def lambda_handler(event, context):

bucket =  'cdn-desabasto'

obj = s3.Object(bucket, key)
data = obj.get()['Body'].read().decode('utf-8')
json_data = json.loads(data)

print(json_data)