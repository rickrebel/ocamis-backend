import csv
import io
from task.aws.common import (
    send_simple_response, calculate_delivered_final, BotoUtils)


# def build_week_csvs(event, context):
def lambda_handler(event, context):
    import traceback

    uniques_aws = BuildWeekAws(event, context)

    # print("before build_week_csvs")
    try:
        final_result = uniques_aws.build_week_csvs()
    except Exception as e:
        print("Exception", e)
        error_ = traceback.format_exc()
        errors = [f"Hay un error raro en la construcción: \n{str(e)}\n{error_}"]
        return send_simple_response(event, context, errors=errors)

    return send_simple_response(event, context, result=final_result)


def get_data_from_row(row, table_file, idx):
    inits = table_file["inits"]
    start = inits[idx]
    try:
        end = inits[idx + 1]
    except IndexError:
        end = None
    return row[start:end]


class BuildWeekAws:

    def __init__(self, event: dict, context):
        self.examples_count = 0
        self.limit_examples = 30

        self.provider_id = event.get("provider_id")
        self.week_record_id = event.get("week_record_id")
        self.is_example = self.week_record_id == 8738
        print("is_example", self.is_example)
        self.week_table_files = event.get("week_table_files", [])
        self.all_inits = {
            "drug": {"field": "uuid", "basic_fields": [
                "week_record_id", "medicament_id"]},
            "rx": {
                "field": "uuid_folio",
                "basic_fields": [
                    "folio_ocamis", "uuid_folio", "delivered_final_id"]
            },
            "unique_helpers": {"field": "medicament_key", "skip": True},
            "complement_drug": {"field": "uuid_comp_drug"},
            "complement_rx": {"field": "uuid_comp_rx"},
            "diagnosis_rx": {"field": "uuid_diag_rx"},
        }

        self.pos_uuid_folio = None

        self.pos_comp_drug = None
        self.pos_final_comp_drug = 200

        self.pos_comp_rx = None

        self.pos_final_main = None

        self.positions = {}
        self.pos_rx_id = 1
        self.pos_delivered = None
        self.sums_by_delivered = {}
        self.drugs_count = 0
        self.diagnosis_rx_count = 0
        self.final_row = {}

        self.headers = {"all": [], "drug": [], "rx": []}
        self.len_drug = 0
        self.real_models = []
        self.csvs = {}
        self.buffers = {}
        self.final_path = event["final_path"]
        basic_models = [
            "drug", "rx", "complement_drug", "complement_rx", "diagnosis_rx"]
        for model in basic_models:
            self.csvs[model] = io.StringIO()
            self.buffers[model] = csv.writer(self.csvs[model], delimiter="|")

        self.s3_utils = BotoUtils(event.get("s3"))

        self.context = context

    def show_examples(self, draw_line=True):
        if not self.is_example:
            return False
        in_limit = self.examples_count < self.limit_examples
        if in_limit:
            if draw_line:
                print("")
            self.examples_count += 1
        return in_limit

    def build_week_csvs(self):
        alone_table_files = [table_file for table_file in self.week_table_files
                             if table_file["sheet_behavior"] == "not_merge"]
        for table_file in alone_table_files:
            self.get_basic_data([table_file])
        uniques_table_files = [
            table_file for table_file in self.week_table_files
            if table_file["sheet_behavior"] == "discard_repeated"]
        if uniques_table_files:
            self.get_basic_data(uniques_table_files, skip_duplicates=True)
        merge_behaviors = ["need_merge", "merged"]
        merge_table_files = [table_file for table_file in self.week_table_files
                             if table_file["sheet_behavior"] in merge_behaviors]
        if merge_table_files:
            self.get_basic_data(merge_table_files)

        print("inside build_week_csvs")
        result = {
            "provider_id": self.provider_id,
            "sums_by_delivered": self.sums_by_delivered,
            "drugs_count": self.drugs_count,
        }
        self.limit_examples += 6
        for model in self.real_models:
            if self.show_examples():
                print(f"model: {model} \n\n{len(self.csvs[model].getvalue())}")
            if model == "diagnosis_rx" and not self.diagnosis_rx_count:
                continue
            name = self.final_path.replace("NEW_ELEM_NAME", model)
            self.s3_utils.save_csv_in_aws(
                self.csvs[model], name, storage_class="STANDARD_IA")
            result[f"{model}_path"] = name

        return result

    def build_headers_and_positions(self, table_file, row):
        if table_file.get("ends"):
            return

        table_file["real_models"] = []
        table_file["inits"] = []
        table_file["needs_added"] = []

        for model, values in self.all_inits.items():
            field = values["field"]
            if field in row:
                index = row.index(field)
                table_file["inits"].append(index)
                table_file["real_models"].append(model)
                if values.get("skip"):
                    continue
                if model not in self.real_models:
                    self.real_models.append(model)
                    table_file["needs_added"].append(model)

        needs_added = table_file["needs_added"]
        for (idx, model) in enumerate(table_file["real_models"]):
            headers = get_data_from_row(row, table_file, idx)
            if model in needs_added:
                # if model == "drug":
                #     headers = [field for field in headers
                #                if field != "week_record_id"]
                #     table_file["len_drug"] = len(headers)
                #     headers.append("week_record_id")
                self.buffers[model].writerow(headers)
                basic_fields = self.all_inits[model].get("basic_fields", [])
                for basic_field in basic_fields:
                    if basic_field in headers:
                        self.positions[basic_field] = headers.index(basic_field)
                    else:
                        print("basic_field", basic_field, headers)
        self.pos_delivered = self.positions.get("delivered_final_id")

        return table_file

    def get_basic_data(self, table_files, skip_duplicates=False):
        # print("skip_duplicates", skip_duplicates)
        every_rows = []
        # every_rows = []
        for table_file in table_files:
            file = table_file["file"]
            csv_content = self.s3_utils.get_object_csv(file)
            real_models = []
            inits = None
            for idx_row, row in enumerate(csv_content):
                current_row = {}
                if not idx_row:
                    table_file = self.build_headers_and_positions(table_file, row)
                    real_models = table_file["real_models"]
                    continue
                for (idx, model) in enumerate(real_models):
                    current_row[model] = get_data_from_row(row, table_file, idx)
                every_rows.append(current_row)

        self.write_basic_tables(every_rows, skip_duplicates)

    def write_basic_tables(self, rows, skip_duplicates=False):
        every_folios = {}
        every_unique_keys = set()
        skips = 0

        for row in rows:
            self.final_row = {}

            self.drugs_count += 1
            sheet_id, folio_ocamis, current_uuid, current_delivered = None, None, None, None
            medicament_id = None
            for model, values in self.all_inits.items():
                data = row.get(model)
                if not data:
                    continue
                basic_fields = values.get("basic_fields", [])
                for basic_field in basic_fields:
                    try:
                        value = data[self.positions.get(basic_field)]
                    except Exception as e:
                        print("positions", self.positions)
                        print("basic_field", basic_field)
                        print("data", data)
                        print("model", model)
                        print("values", values)
                        print("Error", e)
                        raise e
                    if basic_field == "folio_ocamis":
                        folio_ocamis = value
                    elif basic_field == "uuid_folio":
                        current_uuid = value
                    elif basic_field == "delivered_final_id":
                        current_delivered = value
                    elif basic_field == "sheet_file_id":
                        sheet_id = value
                    elif basic_field == "medicament_id":
                        medicament_id = value

                    # if self.show_examples():
                    #     print("basic_field", basic_field, "|", data[self.positions.get(basic_field)])
                    # locals()[basic_field] = data[self.positions.get(basic_field)]
                    # setattr(locals(), basic_field, data[self.positions.get(basic_field)])
                if model == "drug":
                    # data = data[:self.len_drug]
                    # data.append(self.week_record_id)
                    data[-1] = self.week_record_id
                self.final_row[model] = data

            if skip_duplicates:
                unique_key = (folio_ocamis, medicament_id)
                if unique_key in every_unique_keys:
                    skips += 1
                    continue
                every_unique_keys.add(unique_key)

            if folio_ocamis not in every_folios:
                every_folios[folio_ocamis] = {
                    "sheet_ids": {sheet_id},
                    "first_uuid": current_uuid,
                    "first_delivered": current_delivered,
                    "delivered": {current_delivered},
                    "rx_data": self.final_row["rx"],
                }
                self._write_in_buffer("drug", uuid_folio=current_uuid)
                self._write_in_buffer("complement_drug")
                self._write_in_buffer("complement_rx")
                # write_diagnosis_rx()
                self._write_diagnosis_rx()

                continue
            current_folio = every_folios[folio_ocamis]
            # rx_id = row[self.pos_rx_id]
            # prev_rx_id = final_row["drug"][1]
            # if current_folio["first_uuid"] != prev_rx_id:
            #     final_row["drug"][1] = current_folio["first_uuid"]
            self._write_in_buffer("drug", uuid_folio=current_folio["first_uuid"])
            self._write_in_buffer("complement_drug")
            delivered_included = current_delivered in current_folio["delivered"]
            sheet_included = sheet_id in current_folio["sheet_ids"]
            if delivered_included and sheet_included:
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

        self.limit_examples += 1

        for rx in every_folios.values():
            delivered_final = rx["rx_data"][self.pos_delivered]
            self.sums_by_delivered.setdefault(delivered_final, 0)
            self.sums_by_delivered[delivered_final] += 1
            self.buffers["rx"].writerow(rx["rx_data"])

    def _write_in_buffer(self, model_name, uuid_folio=None):
        if row_data := self.final_row.get(model_name):
            if uuid_folio:
                row_data[1] = uuid_folio
            self.buffers[model_name].writerow(row_data)

    def _write_diagnosis_rx(self):
        import uuid as uuid_lib
        if row_data := self.final_row.get("diagnosis_rx"):
            diagnosis_id = row_data[2]
            if not diagnosis_id:
                return
            rx_id = row_data[1]
            all_diagnosis = diagnosis_id.split(";")
            is_main = len(all_diagnosis) == 1
            for diag in all_diagnosis:
                uuid_diag_rx = str(uuid_lib.uuid4())
                diag_data = [uuid_diag_rx, rx_id, diag, is_main]
                self.buffers["diagnosis_rx"].writerow(diag_data)
                self.diagnosis_rx_count += 1
