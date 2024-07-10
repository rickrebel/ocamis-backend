import threading
import time
from datetime import datetime, timedelta

import boto3

from scripts.common import build_s3


def has_enough_balance(task_function) -> bool:

    service = 'cloudwatch'
    credentials = build_s3()
    boto_client = boto3.client(
        service,
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        region_name=credentials["region_aws"],
    )

    start_time_30_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
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
                                'Value': 'new-alldatabases'
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average'
                },
                'ReturnData': True,
            },
        ],
        StartTime=start_time_30_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
        EndTime=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if not type(response) == dict:
        return False

    MetricDataResults = response.get("MetricDataResults", [])
    if not MetricDataResults or not type(MetricDataResults) == list:
        return False
    metric_data = MetricDataResults[0].get("Values", [])

    if not metric_data or not type(metric_data) == list:
        return False

    ebs_percent = metric_data[0]

    return ebs_percent >= task_function.ebs_percent


def delayed_execution(method, delay):
    def wrapper():
        time.sleep(delay)
        method()
    threading.Thread(target=wrapper).start()


def comprobate_waiting_balance():
    from task.models import AsyncTask
    from task.serverless import execute_async
    waiting_balance_task = AsyncTask.objects\
        .filter(status_task_id="queue", task_function__ebs_percent__gt=0)\
        .order_by("id").first()
    if waiting_balance_task:
        if has_enough_balance(waiting_balance_task.task_function):
            execute_async(
                waiting_balance_task, waiting_balance_task.original_request)
        else:
            delayed_execution(comprobate_waiting_balance, 300)
            return
