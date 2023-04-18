import io
import boto3
import csv
import uuid as uuid_lib
import json
import requests
import unidecode
# from .common import obtain_decode

request_headers = {"Content-Type": "application/json"}


def obtain_decode(sample):
    for row in sample:
        is_byte = isinstance(row, bytes)
        posible_latin = False
        if is_byte:
            try:
                row.decode("utf-8")
            except Exception:
                posible_latin = True
            if posible_latin:
                try:
                    row.decode("latin-1")
                    return "latin-1"
                except Exception as e:
                    print(e)
                    return "unknown"
        else:
            return "str"
    return "utf-8"


def text_normalizer(text):
    import re
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)


def calculate_delivered(available_data):
    prescribed_amount = available_data.get("prescribed_amount")
    if not prescribed_amount:
        error = "No se puede determinar el status de entrega;" \
                "No existe cantidad prescrita"
        return available_data, error
    elif prescribed_amount > 30000:
        error = "Existe una cantidad inusualmente alta; cantidad prescrita"
        return available_data, error
    elif prescribed_amount < 0:
        error = "Existe una cantidad negativa; cantidad prescrita"
        return available_data, error

    delivered = "unknown"

    delivered_amount = available_data.get("delivered_amount")
    not_delivered_amount = available_data.pop("not_delivered_amount", None)
    if not_delivered_amount is not None and delivered_amount is None:
        delivered_amount = prescribed_amount - not_delivered_amount
        available_data["delivered_amount"] = delivered_amount

    if delivered_amount is not None:
        if prescribed_amount == delivered_amount:
            delivered = "complete"
        elif not delivered_amount:
            delivered = "denied"
        elif delivered_amount > 30000:
            error = "Existe una cantidad inusualmente alta; cantidad entregada"
            return available_data, error
        elif prescribed_amount > delivered_amount:
            delivered = "partial"
        elif delivered_amount > prescribed_amount:
            delivered = "over_delivered"
        elif delivered_amount < 0:
            error = "Existe una cantidad negativa; cantidad entregada"
            return available_data, error
    else:
        error = "No se puede determinar el status de entrega;" \
                "No existe cantidad entregada"
        return available_data, error
    available_data["delivered_id"] = delivered
    return available_data, None


def calculate_delivered_final(all_delivered):
    some_unknown = [d for d in all_delivered if d == "unknown"]
    if some_unknown:
        return "unknown"
    partials = [d for d in all_delivered if d == "partial"]
    if partials:
        return "partial"
    completes = [d for d in all_delivered if d == "complete"]
    if len(all_delivered) == len(completes):
        return "complete"
    only_denied = [d for d in all_delivered if d == "denied"]
    if len(all_delivered) == len(only_denied):
        return "denied"
    return "partial"


# def start_build_csv_data(event, context={"request_id": "test"}):
def lambda_handler(event, context):
    # if "artificial_request_id" in event:
    #     context["aws_request_id"] = event["artificial_request_id"]
    init_data = event["init_data"]
    init_data["s3"] = event["s3"]
    init_data["webhook_url"] = event.get("webhook_url")
    match_aws = MatchAws(init_data, context)

    aws_access_key_id = event["s3"]["aws_access_key_id"]
    aws_secret_access_key = event["s3"]["aws_secret_access_key"]
    bucket_name = event["s3"]["bucket_name"]
    aws_location = event["s3"]["aws_location"]
    file = event["file"]

    dev_resource = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    content_object = dev_resource.Object(
        bucket_name=bucket_name,
        key=f"{aws_location}/{file}"
    )
    streaming_body_1 = content_object.get()['Body']
    object_final = io.BytesIO(streaming_body_1.read())
    s3_client = boto3.client(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    final_result = match_aws.build_csv_to_data(object_final, s3_client)
    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(webhook_url, data=final_result, headers=request_headers)
    return {
        'statusCode': 200,
        'body': final_result
    }


class MatchAws:

    def __init__(self, init_data: dict, context):
        from datetime import datetime
        for key, value in init_data.items():
            setattr(self, key, value)
        self.sheet_file_id = init_data["sheet_file_id"]
        self.lap_sheet_id = init_data["lap_sheet_id"]
        self.file_name_simple = init_data["file_name_simple"]
        self.sheet_name = init_data["sheet_name"]
        self.final_path = init_data["final_path"]

        self.entity_id = init_data["entity_id"]
        self.global_delegation = init_data["global_delegation"]
        self.global_clues = init_data["global_clues"]

        self.decode = init_data["decode"]
        self.decode_final = 'utf-8'
        self.row_start_data = init_data["row_start_data"]
        self.delimiter = init_data["delimiter"]
        self.string_date = init_data["string_date"]
        self.columns_count = init_data["columns_count"]
        print("string_date", self.string_date)

        self.editable_models = init_data["editable_models"]
        self.real_models = init_data["real_models"]
        self.model_fields = init_data["model_fields"]
        self.hash_null = init_data["hash_null"]
        self.med_cat_models = [cat for cat in self.editable_models
                               if cat.get("app") == "med_cat"]
        self.real_med_cat_models = [cat["name"] for cat in self.med_cat_models
                                    if cat["model"] in self.real_models]
        self.med_cat_flat_fields = {}
        self.initial_data = {}
        for cat_name in self.real_med_cat_models:
            is_med_unit = cat_name == "medical_unit"
            is_medicament = cat_name == "medicament"
            fields = []
            data_values = []
            all_values = []
            for field in self.model_fields[cat_name]:
                field_name = field["name"]
                if field_name == "hex_hash":
                    continue
                value = None
                field["name"] = field_name
                field["default_value"] = None
                if field["is_relation"]:
                    if field_name == "entity_id" and not is_medicament:
                        value = self.entity_id
                        data_values.append(str(value))
                    if is_med_unit:
                        if field_name == "delegation_id" and self.global_delegation:
                            value = self.global_delegation["id"]
                        elif field_name == "clues_id" and self.global_clues:
                            value = self.global_clues["id"]
                    all_values.append(value)
                elif is_med_unit:
                    if field_name == "clues_key" and self.global_clues:
                        field["default_value"] = self.global_clues["clues_key"]
                    elif field_name == "delegation_name" and self.global_delegation:
                        field["default_value"] = self.global_delegation["name"]
                fields.append(field)
            flat_fields = [field for field in fields if not field["is_relation"]]
            self.med_cat_flat_fields[cat_name] = flat_fields
            self.initial_data[cat_name] = {"data_values": data_values,
                                           "all_values": all_values}
        # print("med_cat_flat_fields: \n", self.med_cat_flat_fields)
        self.buffers = {}
        self.csvs = {}
        for model in self.editable_models:
            self.csvs[model["name"]] = io.StringIO()
            self.buffers[model["name"]] = csv.writer(
                self.csvs[model["name"]], delimiter="|")

        self.existing_fields = init_data["existing_fields"]
        self.special_fields = [field for field in self.existing_fields
                               if field["is_special"]]
        self.lap = init_data["lap"]
        self.cat_keys = {}
        for med_cat in self.real_med_cat_models:
            self.cat_keys[med_cat] = set()
        self.webhook_url = init_data.get("webhook_url")

        self.last_revised = datetime.now()

        self.last_missing_row = None
        self.all_missing_rows = []
        self.all_missing_fields = []

        self.s3 = init_data.get("s3")
        self.context = context
        self.last_date = None
        self.last_date_formatted = None
        self.is_prepare = init_data.get("is_prepare", False)

    def build_csv_to_data(self, complete_file, s3_client=None):
        # csv_buffer = {}
        # csv_files = {}
        # for elem in self.editable_models:
        #     csv_files[elem["name"]] = io.StringIO()
        #     csv_buffer[elem["name"]] = csv.writer(
        #         csv_files[elem["name"]], delimiter='|')
        if self.is_prepare:
            complete_file = json.loads(complete_file.read())
            data_rows = complete_file.get("all_data", [])
            tail_data = complete_file.get("tail_data", [])
            data_rows.extend(tail_data)
        else:
            data_rows = complete_file.readlines()
        all_data = self.divide_rows(data_rows)
        for cat in self.editable_models:
            self.build_headers(cat["name"])
        for cat_name in self.real_med_cat_models:
            self.generic_match(cat_name, {}, True)
        # formula_cats = [cat for cat in self.editable_models
        #                 if cat["app"] == "formula"]
        prescription_cats = [cat_name for cat_name in self.real_med_cat_models
                             if cat_name != "medicament"]

        special_cols = self.build_special_cols(all_data)
        required_cols = [col for col in self.existing_fields
                         if col["required_row"]]
        # last_date = None
        # iso_date = None
        # first_iso = None
        all_prescriptions = {}
        success_drugs_count = 0
        total_count = len(all_data)
        processed_count = 0

        discarded_count = self.row_start_data - 1

        for row in all_data[self.row_start_data - 1:]:
            required_cols_in_null = [col for col in required_cols
                                     if not row[col["position"]]]
            if required_cols_in_null:
                discarded_count += 1
                continue
            processed_count += 1
            # print("data_row \t", data_row)
            self.last_missing_row = None
            # is_same_date = False
            uuid = str(uuid_lib.uuid4())

            available_data = {
                "entity_id": self.entity_id,
                "sheet_file_id": self.sheet_file_id,
                "lap_sheet_id": self.lap_sheet_id,
                "row_seq": int(row[0]),
                "uuid": uuid,
            }
            available_data = self.special_available_data(
                available_data, row, special_cols)

            available_data, some_date = self.complement_available_data(
                available_data, row)

            if not some_date:
                error = "Fechas; No se pudo convertir ninguna fecha"
                self.append_missing_row(row, error)
                continue
            # if last_date != date[:10]:
            #     last_date = date[:10]
            iso_date = some_date.isocalendar()
            available_data["iso_year"] = iso_date[0]
            available_data["iso_week"] = iso_date[1]
            available_data["iso_day"] = iso_date[2]
            available_data["month"] = some_date.month
            # if not first_iso:
            #     first_iso = iso_date

            available_data, error = calculate_delivered(available_data)
            if error:
                self.append_missing_row(row, error)
                continue
            delivered = available_data.get("delivered_id")

            available_data = self.generic_match("medicament", available_data)

            folio_document = available_data.get("folio_document")
            folio_ocamis = "%s|%s|%s|%s" % (
                self.entity_id, iso_date[0], iso_date[1], folio_document)

            curr_prescription = all_prescriptions.get(folio_ocamis)
            if curr_prescription:
                available_data["prescription_id"] = curr_prescription["uuid_folio"]
                all_delivered = curr_prescription["all_delivered"]
                all_delivered += [delivered]
                curr_prescription["all_delivered"] = all_delivered
                curr_prescription["delivered_final_id"] = calculate_delivered_final(
                    all_delivered)
            else:
                uuid_folio = str(uuid_lib.uuid4())
                available_data["uuid_folio"] = uuid_folio
                available_data["prescription_id"] = uuid_folio
                available_data["delivered_final_id"] = delivered
                available_data["folio_ocamis"] = folio_ocamis
                available_data["folio_document"] = folio_document
                available_data["all_delivered"] = [delivered]

                for cat_name in prescription_cats:
                    available_data = self.generic_match(
                        cat_name, available_data)

                all_prescriptions[folio_ocamis] = available_data

            current_drug_data = []
            for drug_field in self.model_fields["drug"]:
                value = available_data.pop(drug_field["name"], None)
                if value is None:
                    value = locals().get(drug_field["name"])
                # value = available_data.get(drug_field, locals().get(drug_field))
                current_drug_data.append(value)
            self.buffers["drug"].writerow(current_drug_data)
            success_drugs_count += 1
            # if len(all_prescriptions) > self.sample_size:
            #     break
        final_request_id = self.context.aws_request_id
        report_errors = self.build_report()
        report_errors["prescription_count"] = len(all_prescriptions)
        report_errors["drug_count"] = success_drugs_count
        report_errors["processed_count"] = processed_count
        report_errors["total_count"] = total_count
        report_errors["discarded_count"] = discarded_count
        for med_cat in self.med_cat_models:
            cat_name = med_cat["name"]
            report_errors[f"{cat_name}_count"] = len(self.cat_keys[cat_name]) \
                if self.cat_keys.get(cat_name) else 0
        result_data = {
            "result": {
                "report_errors": report_errors,
                "is_prepare": self.is_prepare,
                "sheet_file_id": self.sheet_file_id,
                "lap_sheet_id": self.lap_sheet_id,
            },
            "request_id": final_request_id
        }
        if self.is_prepare:
            return json.dumps(result_data)

        self.buffers["missing_field"].writerows(self.all_missing_fields)
        self.buffers["missing_row"].writerows(self.all_missing_rows)
        # for cat_name in self.med_cat_models:
        #     cat_values = self.cats.get(cat_name, {}).values()
        #     csv_buffer[cat_name].writerows(cat_values)

        for curr_prescription in all_prescriptions.values():
            current_prescription_data = []
            # curr_prescription = all_prescriptions.get(folio)
            for field_p in self.model_fields["prescription"]:
                value = curr_prescription.get(field_p["name"])
                current_prescription_data.append(value)
            self.buffers["prescription"].writerow(current_prescription_data)

        bucket_name = self.s3.get("bucket_name")
        aws_location = self.s3.get("aws_location")

        all_final_paths = []

        for elem_list in self.editable_models:
            cat_name = elem_list["name"]
            if "missing" in cat_name:
                cat_count = report_errors.get(f"{cat_name}s", 0)
            else:
                cat_count = report_errors.get(f"{cat_name}_count", 0)
            if cat_count == 0:
                continue
            only_name = self.final_path.replace("NEW_ELEM_NAME", cat_name)
            all_final_paths.append({
                "name": cat_name,
                "model": elem_list["model"],
                "path": only_name,
            })
            s3_client.put_object(
                Body=self.csvs[cat_name].getvalue(),
                Bucket=bucket_name,
                Key=f"{aws_location}/{only_name}",
                ContentType="text/csv",
                ACL="public-read",
            )
            # self.send_csv_to_db(final_path, elem_list)

        result_data["result"]["final_paths"] = all_final_paths
        result_data["result"]["decode"] = self.decode
        return json.dumps(result_data)

    def get_json_file(self, file_name):
        aws_access_key_id = self.s3["aws_access_key_id"]
        aws_secret_access_key = self.s3["aws_secret_access_key"]
        bucket_name = self.s3["bucket_name"]
        aws_location = self.s3["aws_location"]

        s3_client = boto3.client(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        obj = s3_client.get_object(
            Bucket=bucket_name,
            Key=f"{aws_location}/{file_name}")
        return json.loads(obj['Body'].read().decode('utf-8'))

    def divide_rows(self, data_rows):
        structured_data = []
        sample = data_rows[:50]
        self.decode = self.decode or obtain_decode(sample)
        if self.decode == "latin-1":
            self.decode_final = 'latin-1'

        if self.decode == "unknown":
            error = "No se pudo decodificar el archivo"
            return [], [error], None

        # for row_seq, row in enumerate(data_rows[begin+1:], start=begin+1):
        for row_seq, row in enumerate(data_rows, start=1):
            self.last_missing_row = None
            if self.is_prepare:
                row_data = [col.replace('\r\n', '').strip() for col in row]
            else:
                row_decode = row.decode(self.decode) if self.decode != "str" else str(row)
                # .replace('\r\n', '')
                row_data = row_decode.replace('\r\n', '').split(self.delimiter or '|')
            current_count = len(row_data)
            row_data.insert(0, str(row_seq))
            if current_count == self.columns_count:
                structured_data.append(row_data)
            else:
                error = "Conteo distinto de Columnas; %s de %s" % (
                    current_count, self.columns_count)
                self.append_missing_row(row_data, error)

        return structured_data

    def build_special_cols(self, all_data):

        def get_columns_by_type(column_type):
            return [col for col in self.existing_fields
                    if col["column_type"] == column_type]

        return {
            "built": self.get_built_cols(),
            "divided": self.get_divided_cols(),
            "global": get_columns_by_type("global"),
            "tab": get_columns_by_type("tab"),
            "file_name": get_columns_by_type("file_name"),
            "ceil": self.get_ceil_cols(all_data)
        }

    def get_built_cols(self):
        built_cols = []
        base_built_cols = [col for col in self.existing_fields
                           if col["column_type"] == "built"]
        for built_col in base_built_cols:
            origin_cols = [col for col in self.existing_fields
                           if col["child"] == built_col["name_column"]]
            origin_cols = sorted(origin_cols, key=lambda x: x.get("t_value"))
            built_col["origin_cols"] = origin_cols
            built_cols.append(built_col)
        return built_cols

    def get_divided_cols(self):
        divided_cols = []
        base_divided_cols = [col for col in self.existing_fields
                             if col["column_type"] == "divided"]
        unique_parents = list(set([col["name_column"]
                                   for col in base_divided_cols]))
        for parent in unique_parents:
            try:
                parent_col = [col for col in self.existing_fields
                              if col["name_column"] == parent][0]
            except IndexError:
                continue
            destiny_cols = [col for col in base_divided_cols
                            if col["name_column"] == parent]
            destiny_cols = sorted(destiny_cols, key=lambda x: x.get("t_value"))
            parent_col["destiny_cols"] = destiny_cols
            divided_cols.append(parent_col)
        return divided_cols

    def get_ceil_cols(self, all_data):
        ceil_cols = []
        ceil_excel_cols = [col for col in self.existing_fields
                           if col["column_type"] == 'ceil_excel']
        for col in ceil_excel_cols:
            ceil = col.get("t_value")
            if not ceil:
                continue
            row_position = int(ceil[1:])
            col_position = ord(ceil[0]) - 64
            col["final_value"] = all_data[row_position - 1][col_position]
            ceil_cols.append(col)
        return ceil_cols

    def special_available_data(self, available_data, row, special_cols):

        for built_col in special_cols["built"]:
            origin_values = []
            for origin_col in built_col["origin_cols"]:
                origin_values.append(row[origin_col["position"]])
            concat_char = built_col.get("t_value", "")
            built_value = concat_char.join(origin_values)
            available_data[built_col["name"]] = built_value

        for divided_col in special_cols["divided"]:
            divided_char = divided_col.get("t_value")
            if not divided_char:
                continue
            origin_value = row[divided_col["position"]]
            divided_values = origin_value.split(divided_char)
            destiny_cols = divided_col["destiny_cols"]
            for i, divided_value in enumerate(divided_values, start=1):
                destiny_col = destiny_cols[i - 1]
                available_data[destiny_col["name"]] = divided_value

        for global_col in special_cols["global"]:
            available_data[global_col["name"]] = global_col["t_value"]

        for tab_col in special_cols["tab"]:
            available_data[tab_col["name"]] = self.sheet_name

        for file_name_col in special_cols["file_name"]:
            available_data[file_name_col["name"]] = self.file_name_simple

        for ceil_col in special_cols["ceil"]:
            available_data[ceil_col["name"]] = ceil_col["final_value"]
        return available_data

    def complement_available_data(self, available_data, row):
        from datetime import datetime, timedelta
        import re

        some_date = None
        uuid = available_data.get("uuid")
        # fields_with_name = [field for field in self.existing_fields
        #                     if field["name"] and field["position"]]
        fields_with_name = [field for field in self.existing_fields
                            if field["name"]]
        for field in fields_with_name:
            error = None
            if field.get("position"):
                value = row[field["position"]]
            else:
                value = available_data.get(field["name"])
                if not value:
                    continue
            if field.get("duplicated_in"):
                duplicated_in = field["duplicated_in"]
                duplicated_value = row[duplicated_in["position"]]
                if duplicated_value != value:
                    error = f"El valor de las columnas que apuntan a " \
                            f"{field['name']} no coinciden"
            try:
                if field["data_type"] == "Datetime":  # and not is_same_date:
                    if value == self.last_date and value:
                        value = self.last_date_formatted
                    elif self.string_date == "EXCEL":
                        self.last_date = value
                        days = int(value)
                        seconds = (value - days) * 86400
                        seconds = round(seconds)
                        value = datetime(1899, 12, 30) + timedelta(
                            days=days, seconds=seconds)
                        self.last_date_formatted = value
                    else:
                        self.last_date = value
                        value = datetime.strptime(value, self.string_date)
                        self.last_date_formatted = value
                    if not some_date:
                        some_date = value
                elif field["data_type"] == "Integer":
                    value = int(value)
                elif field["data_type"] == "Float":
                    value = float(value)
            except ValueError:
                error = "No se pudo convertir a %s" % field["data_type"]
            if value and not error:
                regex_format = field.get("regex_format")
                if regex_format:
                    if not re.match(regex_format, value):
                        error = "No se validó con el formato de %s" % field["name"]
                elif field.get("max_length"):
                    if len(value) > field["max_length"]:
                        error = "El valor tiene más de los caracteres permitidos"
                clean_function = field.get("clean_function")
                if clean_function:
                    if clean_function == "almost_empty":
                        value = None
                    elif clean_function == "text_nulls":
                        if value == field.get("t_value"):
                            value = None
            if error:
                self.append_missing_field(
                    row, field["name_column"], value, error=error, drug_uuid=uuid)
                value = None
            available_data[field["name"]] = value
        return available_data, some_date

    def build_headers(self, cat_name):
        fields = self.model_fields[cat_name]
        headers = [field["name"] for field in fields]
        self.buffers[cat_name].writerow(headers)

    def generic_match(self, cat_name, available_data, is_first=False):
        import hashlib
        flat_fields = self.med_cat_flat_fields.get(cat_name, {})
        init_values = self.initial_data.get(cat_name, {})
        initial_all_values = init_values.get("all_values", []).copy()
        initial_data_values = init_values.get("data_values", []).copy()
        all_values = []
        data_values = []
        is_med_unit = cat_name == "medical_unit"
        is_medicament = cat_name == "medicament"
        for flat_field in flat_fields:
            field_name = flat_field["name"]
            value = available_data.pop(f"{cat_name}_{field_name}", None)
            if value and is_medicament:
                if field_name == "key2":
                    value = value.replace(".", "")
                if field_name == "own_key2":
                    all_values[0] = self.entity_id
            elif is_med_unit and not value:
                value = flat_field["default_value"]
            if value is not None:
                str_value = value if flat_field["is_string"] else str(value)
                data_values.append(str_value)
            all_values.append(value)

        def add_hash_to_cat(hash_key, flat_values):
            if is_first or hash_key not in self.cat_keys[cat_name]:
                every_values = [hash_key] + initial_all_values + flat_values
                self.buffers[cat_name].writerow(every_values)
                self.cat_keys[cat_name].add(hash_key)

        if not data_values:
            hash_id = None
            # if is_first:
            #     add_hash_to_cat(self.hash_null, all_values)
        else:
            final_data_values = initial_data_values + data_values
            value_string = "".join(final_data_values)
            value_string = value_string.encode(self.decode_final)
            hash_id = hashlib.md5(value_string).hexdigest()
            add_hash_to_cat(hash_id, all_values)
        available_data[f"{cat_name}_id"] = hash_id
        return available_data

    def append_missing_row(self, row_data, error=None, drug_id=None):
        if self.last_missing_row:
            if error:
                self.last_missing_row[-2] = False
                self.all_missing_rows[-1][-1] = error
            return self.all_missing_rows[-1][0]
        last_revised = self.last_revised
        inserted = not bool(error)
        inserted = False
        # row_seq = int(row_data[0])
        # original_data = row_data[1:]
        original_data = json.dumps(row_data)
        missing_data = []
        uuid = str(uuid_lib.uuid4())
        sheet_file_id = self.sheet_file_id
        lap_sheet_id = self.lap_sheet_id
        lap_sheet_id = self.lap_sheet_id
        for field in self.model_fields["missing_row"]:
            value = locals().get(field["name"])
            missing_data.append(value)
        self.last_missing_row = missing_data
        self.all_missing_rows.append(missing_data)
        return uuid

    def append_missing_field(
            self, row, name_column_id, original_value, error, drug_uuid=None):
        missing_row_id = self.append_missing_row(row, drug_id=drug_uuid)
        missing_field = []
        uuid = str(uuid_lib.uuid4())
        inserted = False
        last_revised = self.last_revised
        # if name_column:
        #     name_column = name_column.id
        for field in self.model_fields["missing_field"]:
            value = locals().get(field["name"])
            missing_field.append(value)
        self.all_missing_fields.append(missing_field)

    def build_report(self):
        report_data = {"general_errors": ""}
        if self.all_missing_rows:
            report_data["missing_rows"] = len(self.all_missing_rows)
            row_errors = {}
            error_types_count = 0
            for missing_row in self.all_missing_rows:
                error = missing_row[-1]
                if not error:
                    continue
                try:
                    [error_type, error_detail] = error.split(";", 1)
                except Exception as e:
                    # print("error report:", e)
                    [error_type, error_detail] = [error, "GENERAL"]
                if error_type in row_errors:
                    row_errors[error_type]["count"] += 1
                    if error_detail in row_errors[error_type]:
                        row_errors[error_type][error_detail]["count"] += 1
                        example_count = len(
                            row_errors[error_type][error_detail]["examples"])
                        if example_count < 4:
                            row_errors[error_type][error_detail]["examples"].append(
                                missing_row[-3])
                    elif len(row_errors[error_type]) < 20:
                        row_errors[error_type][error_detail] = {
                            "count": 1, "examples": [missing_row[-3]]}
                elif error_types_count < 40:
                    row_errors[error_type] = {
                        "count": 1,
                        error_detail: {
                            "count": 1, "examples": [missing_row[-3]]}
                    }
                    error_types_count += 1
            # row_errors = sorted(row_errors.items(), key=lambda x: x[1], reverse=True)
            # row_errors = row_errors[:50]
            report_data["row_errors"] = row_errors
            if len(row_errors) > 50:
                report_data["general_errors"] += \
                    "Se encontraron más de 50 tipos de errores en las filas"
        else:
            report_data["missing_rows"] = 0
            report_data["row_errors"] = {}

        if self.all_missing_fields:
            report_data["missing_fields"] = len(self.all_missing_fields)
            field_errors = {}
            error_types_count = 0
            for missing_field in self.all_missing_fields:
                error = missing_field[-1]
                name_column = missing_field[2]
                original_value = missing_field[3]
                if error in field_errors:
                    field_errors[error]["count"] += 1
                    if name_column in field_errors[error]:
                        field_errors[error][name_column]["count"] += 1
                        examples = field_errors[error][name_column]["examples"]
                        if len(examples) < 6 and original_value not in examples:
                            field_errors[error][name_column]["examples"].append(
                                original_value)
                    else:
                        field_errors[error][name_column] = {
                            "count": 1,
                            "examples": [original_value]
                        }
                elif error_types_count < 40:
                    error_types_count += 1
                    field_errors[error] = {
                        "count": 1,
                        name_column: {
                            "count": 1,
                            "examples": [original_value]
                        }
                    }
            # field_errors = sorted(
            #     # field_errors.items(), key=lambda x: sum(x[1].values()),
            #     field_errors.items(), key=lambda x: sum(x["count"].values()),
            #     reverse=True)
            report_data["field_errors"] = field_errors
        else:
            report_data["missing_fields"] = 0
            report_data["field_errors"] = {}

        if not report_data.get("missing_rows") and not report_data.get("missing_fields"):
            report_data["general_errors"] = "No se encontraron errores"
        return report_data
