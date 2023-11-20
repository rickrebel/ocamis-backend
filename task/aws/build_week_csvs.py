import csv
import io
from task.aws.common import (
    send_simple_response, calculate_delivered_final, BotoUtils)


# def build_week_csvs(event, context):
def lambda_handler(event, context):
    uniques_aws = BuildWeekAws(event, context)
    print("before build_week_csvs")
    final_result = uniques_aws.build_week_csvs()
    return send_simple_response(event, context, result=final_result)


class BuildWeekAws:

    def __init__(self, event: dict, context):

        self.entity_id = event.get("entity_id")
        self.entity_week_id = event.get("entity_week_id")
        self.week_table_files = event.get("week_table_files", [])
        self.pos_uuid_folio = None
        self.pos_comp_drug = None
        self.pos_comp_rx = None
        self.pos_final_main = None
        self.pos_final_comp_drug = 200
        self.positions = {}
        self.pos_rx_id = 1
        self.pos_delivered = None
        self.sums_by_delivered = {}
        self.drugs_count = 0

        self.headers = {"all": [], "drug": [], "rx": []}
        self.len_drug = 0
        self.basic_fields = [
            "sheet_file_id", "folio_ocamis", "uuid_folio", "delivered_final_id"]
        self.basic_models = ["drug", "rx", "complement_drug", "complement_rx"]
        self.real_models = ["drug", "rx"]
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
        result = {
            "entity_id": self.entity_id,
            "sums_by_delivered": self.sums_by_delivered,
            "drugs_count": self.drugs_count,
        }
        for model in self.real_models:
            name = self.final_path.replace("NEW_ELEM_NAME", model)
            self.s3_utils.save_file_in_aws(self.csvs[model].getvalue(), name)
            result[f"{model}_path"] = name

        return result

    def build_headers_and_positions(self, row):
        if self.pos_uuid_folio is None:
            self.headers["all"] = row
            header_comp_drug = None
            try:
                self.pos_comp_drug = row.index("uuid_comp_drug")
                self.pos_final_main = self.pos_comp_drug
                header_comp_drug = row[self.pos_comp_drug:]
                self.real_models.append("complement_drug")
            except Exception as e:
                print("error pos_comp_drug", e)
            try:
                self.pos_comp_rx = row.index("uuid_comp_rx")
                self.pos_final_comp_drug = self.pos_comp_rx
                self.buffers["complement_rx"] = row[self.pos_comp_rx:]
                self.real_models.append("complement_rx")
                if self.pos_comp_drug:
                    header_comp_drug = row[self.pos_comp_drug:self.pos_comp_rx]
                else:
                    self.pos_final_main = self.pos_comp_rx
            except Exception as e:
                print("error pos_comp_rx", e)
                if not self.pos_final_main:
                    self.pos_final_main = 200

            if self.pos_comp_drug:
                self.buffers["complement_drug"].writerow(header_comp_drug)

            self.pos_uuid_folio = row.index("uuid_folio")
            for b_field in self.basic_fields:
                self.positions[b_field] = row.index(b_field)
            self.headers["drug"] = row[:self.pos_uuid_folio]
            self.headers["drug"] = [field for field in self.headers["drug"]
                                    if field != "entity_week_id"]
            self.len_drug = len(self.headers["drug"])
            self.headers["drug"].append("entity_week_id")
            self.buffers["drug"].writerow(self.headers["drug"])
            self.headers["rx"] = row[self.pos_uuid_folio:self.pos_final_main]
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
            self.drugs_count += 1
            current_drug = row[:self.len_drug]
            current_drug.append(self.entity_week_id)
            current_comp_drug = None
            if self.pos_comp_drug:
                current_comp_drug = row[self.pos_comp_drug:self.pos_final_comp_drug]

            if folio_ocamis not in every_folios:
                current_comp_rx = None
                if self.pos_comp_rx:
                    current_comp_rx = row[self.pos_comp_rx:]
                every_folios[folio_ocamis] = {
                    "sheet_ids": {sheet_id},
                    "first_uuid": current_uuid,
                    "first_delivered": current_delivered,
                    "delivered": {current_delivered},
                    "rx_data": row[self.pos_uuid_folio:self.pos_final_main],
                    "complement_rx": current_comp_rx,
                }
                self.buffers["drug"].writerow(current_drug)
                if current_comp_drug:
                    self.buffers["complement_drug"].writerow(current_comp_drug)
                continue
            current_folio = every_folios[folio_ocamis]
            rx_id = row[self.pos_rx_id]
            if current_folio["first_uuid"] != rx_id:
                current_drug[self.pos_rx_id] = current_folio["first_uuid"]
            self.buffers["drug"].writerow(current_drug)
            if current_comp_drug:
                self.buffers["complement_drug"].writerow(current_comp_drug)
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
            delivered_final = rx["rx_data"][self.pos_delivered]
            self.sums_by_delivered[delivered_final] = \
                self.sums_by_delivered.get(delivered_final, 0) + 1
            self.buffers["rx"].writerow(rx["rx_data"])
            if self.pos_comp_rx:
                self.buffers["complement_rx"].writerow(rx["complement_rx"])
