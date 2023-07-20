import requests
import json
import csv
import io
from task.aws.common import request_headers, BotoUtils


# def rebuild_week_csv(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))

    uniques_aws = RebuildWeekAws(event, context)
    # print("before build_week_csvs")
    final_result = uniques_aws.rebuild_week_csv()
    json_result = json.dumps(final_result)
    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(webhook_url, data=json_result, headers=request_headers)
    return {
        'statusCode': 200,
        'body': json_result
    }


class RebuildWeekAws:

    def __init__(self, event: dict, context):

        self.entity_week_id = str(event["entity_week_id"])
        self.final_path = event["final_path"]
        self.csv = io.StringIO()
        self.buffer = csv.writer(self.csv, delimiter="|")
        self.s3_utils = BotoUtils(event.get("s3"))

        self.context = context

    def rebuild_week_csv(self):
        csv_content = self.s3_utils.get_object_file(self.final_path)
        # headers = next(csv_content)
        # print("headers", headers)
        current_rows = []
        total_rows = 0
        example_prints = 0
        for idx, row in enumerate(csv_content):
            if not idx:
                row.append("entity_week_id")
            else:
                row.append(self.entity_week_id)
                total_rows += 1
            if example_prints < 10:
                print("row", row)
                example_prints += 1
            current_rows.append(row)
        self.buffer.writerows(current_rows)
        self.s3_utils.save_file_in_aws(self.csv.getvalue(), self.final_path)
        errors = []
        result_data = {
            "result": {
                "entity_week_id": self.entity_week_id,
                "drugs_count": total_rows - 1,
                "success": bool(not errors)
            },
            "request_id": self.context.aws_request_id
        }

        return result_data
