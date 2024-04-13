import boto3
from scripts.common import build_s3, start_session
from datetime import datetime, timedelta

service = 'cloudwatch'
credentials = build_s3()
# print("credentials", credentials)
AWS_S3_REGION_NAME = 'us-west-2'
boto_client = boto3.client(
    service,
    aws_access_key_id=credentials["aws_access_key_id"],
    aws_secret_access_key=credentials["aws_secret_access_key"],
    region_name=credentials["region_aws"],
)

start_time_30_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
response = boto_client.get_metric_data(
    MetricDataQueries=[
        {
            'Id': 'm1',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/RDS',
                    'MetricName': 'EBSByteBalance%',
                    'Dimensions': [
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': 'alldatabases'
                        },
                    ]
                },
                'Period': 60,
                'Stat': 'Average'
            },
            'ReturnData': True,
        },
    ],
    # StartTime='2023-07-20T00:00:00Z', # Adjust your start time as needed
    StartTime=start_time_30_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
    EndTime=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
)

print(response)

