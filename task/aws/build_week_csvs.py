import requests
import json
import csv
import io
from task.aws.common import (
    request_headers, calculate_delivered_final, BotoUtils)


# def build_week_csvs(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))

    uniques_aws = BuildWeekAws(event, context)
    print("before build_week_csvs")
    final_result = uniques_aws.build_week_csvs()
    json_result = json.dumps(final_result)
    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(webhook_url, data=json_result, headers=request_headers)
    return {
        'statusCode': 200,
        'body': json_result
    }


class BuildWeekAws:

    def __init__(self, event: dict, context):

        self.entity_id = event.get("entity_id")
        self.week_table_files = event.get("week_table_files", [])
        self.pos_uuid_folio = None
        self.positions = {}
        self.pos_rx_id = 1
        self.pos_delivered = None

        self.headers = {"all": [], "drug": [], "rx": []}
        self.basic_fields = [
            "sheet_file_id", "folio_ocamis", "uuid_folio", "delivered_final_id"]
        self.basic_models = ["drug", "rx"]
        self.csvs = {}
        self.buffers = {}
        self.final_path = event["final_path"]
        for model in self.basic_models:
            self.csvs[model] = io.StringIO()
            self.buffers[model] = csv.writer(self.csvs[model], delimiter="|")

        self.s3_utils = BotoUtils(event.get("s3"))

        self.context = context

    def build_week_csvs(self):
        alone_table_files = [table_file for table_file in self.week_table_files
                             if table_file["sheet_behavior"] == "not_merge"]
        self.get_basic_data(alone_table_files)
        merge_behaviors = ["need_merge", "merged"]
        merge_table_files = [table_file for table_file in self.week_table_files
                             if table_file["sheet_behavior"] in merge_behaviors]
        merge_rows = self.get_basic_data(merge_table_files, True)
        self.write_basic_tables(merge_rows)

        print("inside build_week_csvs")
        name_drug = self.final_path.replace("NEW_ELEM_NAME", "drug")
        self.s3_utils.save_file_in_aws(self.csvs["drug"].getvalue(), name_drug)
        name_rx = self.final_path.replace("NEW_ELEM_NAME", "rx")
        self.s3_utils.save_file_in_aws(self.csvs["rx"].getvalue(), name_rx)
        errors = []
        result_data = {
            "result": {
                "entity_id": self.entity_id,
                "drug_path": name_drug,
                "rx_path": name_rx,
                "errors": errors,
                "success": bool(not errors)
            },
            "request_id": self.context.aws_request_id
        }

        return result_data

    def build_headers_and_positions(self, row):
        if self.pos_uuid_folio is None:
            self.headers["all"] = row
            self.pos_uuid_folio = row.index("uuid_folio")
            for b_field in self.basic_fields:
                self.positions[b_field] = row.index(b_field)
            self.headers["drug"] = row[:self.pos_uuid_folio]
            self.buffers["drug"].writerow(self.headers["drug"])
            self.headers["rx"] = row[self.pos_uuid_folio:]
            self.buffers["rx"].writerow(self.headers["rx"])
            self.pos_delivered = \
                self.positions.get("delivered_final_id") - self.pos_uuid_folio

    def get_basic_data(self, table_files, is_merge=False):
        every_rows = []
        for table_file in table_files:
            current_rows = []
            file = table_file["file"]
            csv_content = self.s3_utils.get_object_file(file)
            for idx, row in enumerate(csv_content):
                if not idx:
                    self.build_headers_and_positions(row)
                    continue
                if is_merge:
                    every_rows.append(row)
                else:
                    current_rows.append(row)
                    # self.buffers["drug"].writerow(row[:self.pos_uuid_folio])
                    # self.buffers["rx"].writerow(row[self.pos_uuid_folio:])
            if not is_merge:
                self.write_basic_tables(current_rows)

        return every_rows

    def write_basic_tables(self, rows):
        every_folios = {}
        for row in rows:
            current_util = []
            for field in self.basic_fields:
                current_util.append(row[self.positions.get(field)])
            sheet_id, folio_ocamis, current_uuid, current_delivered = current_util
            current_drug = row[:self.pos_uuid_folio]
            if folio_ocamis not in every_folios:
                every_folios[folio_ocamis] = {
                    "sheet_ids": {sheet_id},
                    "first_uuid": current_uuid,
                    "first_delivered": current_delivered,
                    "delivered": {current_delivered},
                    "rx_data": row[self.pos_uuid_folio:]
                }
                self.buffers["drug"].writerow(current_drug)
                continue
            current_folio = every_folios[folio_ocamis]
            rx_id = row[self.pos_rx_id]
            if current_folio["first_uuid"] != rx_id:
                current_drug[self.pos_rx_id] = current_folio["first_uuid"]
            self.buffers["drug"].writerow(current_drug)
            del_included = current_delivered in current_folio["delivered"]
            sheet_included = sheet_id in current_folio["sheet_ids"]
            if del_included and sheet_included:
                continue
            current_folio["delivered"].add(current_delivered)
            current_folio["sheet_ids"].add(sheet_id)
            if len(current_folio["delivered"]) > 1:
                delivered, err = calculate_delivered_final(
                    current_folio["delivered"])
                if delivered != current_folio["first_delivered"]:
                    current_folio["first_delivered"] = delivered
                    current_folio["rx_data"][self.pos_delivered] = delivered
            every_folios[folio_ocamis] = current_folio
        for rx in every_folios.values():
            self.buffers["rx"].writerow(rx["rx_data"])
