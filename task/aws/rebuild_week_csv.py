import csv
import io
from task.aws.common import send_simple_response, BotoUtils


# def rebuild_week_csv(event, context):
def lambda_handler(event, context):

    uniques_aws = RebuildWeekAws(event, context)
    # print("before build_week_csvs")
    is_enumerate = event.get("is_enumerate", False)
    if is_enumerate:
        uniques_aws.rebuild_mats_csv()
        return {
            'statusCode': 200,
            'body': {"ok": True}
        }
    else:
        final_result = uniques_aws.rebuild_week_csv()
        return send_simple_response(event, context, result=final_result)


class RebuildWeekAws:

    def __init__(self, event: dict, context):

        self.week_record_id = str(event.get("week_record_id"))
        self.final_path = event["final_path"]
        self.result_path = event.get("result_path", self.final_path)
        self.csv = io.StringIO()
        self.buffer = csv.writer(self.csv, delimiter="|")
        self.s3_utils = BotoUtils(event.get("s3"))

        self.context = context

    def rebuild_mats_csv(self):
        csv_content = self.s3_utils.get_object_csv(
            self.final_path, delimiter=",")
        current_rows = []
        has_id = False
        for idx, row in enumerate(csv_content):
            if not idx:
                has_id = "id" in row
                if not has_id:
                    new_row = ["id"] + row
                else:
                    new_row = row
            else:
                if not has_id:
                    row = [idx] + row
                new_row = []
                for value in row:
                    if value == "NULL":
                        value = None
                    new_row.append(value)
            current_rows.append(new_row)
        self.buffer.writerows(current_rows)
        self.s3_utils.save_csv_in_aws(self.csv, self.result_path)
        return {}

    def rebuild_week_csv(self):
        csv_content = self.s3_utils.get_object_csv(self.final_path)
        # headers = next(csv_content)
        # print("headers", headers)
        current_rows = []
        total_rows = 0
        example_prints = 0
        len_rows = 0
        for idx, row in enumerate(csv_content):
            if not idx:
                row = [field for field in row
                       if field != "week_record_id"]
                len_rows = len(row)
                row.append("week_record_id")
            else:
                row = row[:len_rows]
                if len(row) < len_rows:
                    row.append(None)
                # row.append(None)
                row.append(self.week_record_id)
                total_rows += 1
            if example_prints < 10:
                print("row", row)
                example_prints += 1
            current_rows.append(row)
        self.buffer.writerows(current_rows)
        self.s3_utils.save_csv_in_aws(self.csv, self.final_path)
        result = {
            "week_record_id": self.week_record_id,
            "drugs_count": total_rows
        }
        return result
