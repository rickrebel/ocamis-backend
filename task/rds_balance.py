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


def delayed_execution(method, delay, **kwargs):
    def wrapper():
        time.sleep(delay)
        method(**kwargs)
    threading.Thread(target=wrapper).start()


def comprobate_waiting_balance(force=True, **kwargs):
    from task.serverless import TaskChecker
    task_checker = TaskChecker()
    task_checker.comprobate_ebs(force=force)


def comprobate_waiting_balance_old():
    from task.models import AsyncTask
    from task.serverless import Serverless
    waiting_balance_task = AsyncTask.objects.in_queue(ebs=True).first()
    if waiting_balance_task:
        if has_enough_balance(waiting_balance_task.task_function):
            serverless_task = Serverless(waiting_balance_task)
            serverless_task.execute_async()
        else:
            delayed_execution(comprobate_waiting_balance_old, 300)
            return
