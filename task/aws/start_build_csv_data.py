import io
import boto3
import csv
import uuid as uuid_lib
import json
import requests
import unidecode

delegation_value_list = [
    'name', 'other_names', 'state__short_name', 'id', 'clues']
request_headers = {"Content-Type": "application/json"}


def text_normalizer(text):
    import re
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)


def calculate_delivered(available_data):
    prescribed_amount = available_data.get("prescribed_amount")
    if not prescribed_amount:
        error = "No se pudo determinar si se entregó o no"
        return available_data, error

    delivered = "unknown"

    delivered_amount = available_data.get("delivered_amount")
    not_delivered_amount = available_data.pop("not_delivered_amount", None)
    if not_delivered_amount is not None and delivered_amount is None:
        delivered_amount = prescribed_amount - not_delivered_amount
        available_data["delivered_amount"] = delivered_amount

    if prescribed_amount and delivered_amount is not None:
        if prescribed_amount == delivered_amount:
            delivered = "complete"
        elif not delivered_amount:
            delivered = "denied"
        elif prescribed_amount > delivered_amount:
            delivered = "partial"
    else:
        error = "No se pudo determinar si se entregó o no"
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
    is_prepare = init_data.get("is_prepare", False)
    # if init_data.get("is_prepare", False):
    #     prepare_sample = init_data["sample_data"]
    #     final_result = match_aws.build_csv_to_data(prepare_sample)
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
    # print("final_result", final_result)
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
        self.data_file_id = init_data["data_file_id"]
        self.file_name = init_data["file_name"]
        self.sheet_name = init_data["sheet_name"]
        # self.file_control_id = init_data["file_control_id"]
        self.global_clues_id = init_data["global_clues_id"]
        self.agency_id = init_data["agency_id"]
        self.institution_id = init_data["institution_id"]
        # self.global_state_id = init_data["global_state_id"]
        self.global_delegation_id = init_data["global_delegation_id"]
        self.decode = init_data["decode"]
        self.final_path = init_data["final_path"]
        self.row_start_data = init_data["row_start_data"]
        self.delimiter = init_data["delimiter"]
        self.columns_count = init_data["columns_count"]
        self.editable_models = init_data["editable_models"]
        self.model_fields = init_data["model_fields"]
        self.existing_fields = init_data["existing_fields"]
        self.special_fields = [field for field in self.existing_fields
                               if field["is_special"]]
        self.lap = init_data["lap"]

        self.catalogs = init_data["catalogs"]
        self.cats = {}
        # self.catalog_clues = {}
        # self.catalog_container = {}
        # self.catalog_delegation = {}
        self.webhook_url = init_data.get("webhook_url")

        self.string_date = init_data["string_date"]
        # self.unique_clues = init_data["unique_clues"]
        self.failed_delegations = []

        self.last_revised = datetime.now()

        self.last_missing_row = None
        self.all_missing_rows = []
        self.all_missing_fields = []
        self.new_cat_rows = {cat: [] for cat in self.catalogs.keys()}

        self.s3 = init_data.get("s3")
        self.context = context
        self.total_tries = 1
        self.last_date = None
        self.last_date_formatted = None

        self.is_prepare = init_data.get("is_prepare", False)

    def build_csv_to_data(self, complete_file, s3_client=None):
        csv_buffer = {}
        csv_files = {}
        for elem in self.editable_models:
            csv_files[elem["name"]] = io.StringIO()
            csv_buffer[elem["name"]] = csv.writer(
                csv_files[elem["name"]], delimiter=self.delimiter)
        print("PASO 1")
        if self.is_prepare:
            complete_file = json.loads(complete_file.read())
            data_rows = complete_file.get("all_data", [])
            tail_data = complete_file.get("tail_data", [])
            data_rows.extend(tail_data)
        else:
            data_rows = complete_file.readlines()
        print("PASO 2")
        all_data = self.divide_rows(data_rows)

        print("PASO 3")
        for cat_name, cat_data in self.catalogs.items():
            print(f"PASO 3.{cat_name}")
            # print("cat_unique", cat_data["unique_field"])
            # print("cat_unique_id", cat_data["unique_field_id"])
            try:
                current_unique = [field for field in self.existing_fields if
                                  field["final_field_id"] == cat_data["unique_field_id"]][0]
            except IndexError:
                current_unique = {}
            self.catalogs[cat_name]["unique_field"] = current_unique
            current_json = self.get_json_file(cat_data.get("file"))
            self.cats[cat_name] = current_json

        required_cols = [col for col in self.existing_fields
                         if col["required_row"]]
        built_cols = self.get_built_cols()
        divided_cols = self.get_divided_cols()
        file_name = self.file_name.split(".")[0]
        global_cols = [col for col in self.existing_fields
                       if col["column_type"] == "global"]
        tab_cols = [col for col in self.existing_fields
                    if col["column_type"] == "tab"]
        file_name_cols = [col for col in self.existing_fields
                          if col["column_type"] == 'file_name']
        ceil_cols = self.get_ceil_cols(all_data)
        print("PASO 4")
        # last_date = None
        # iso_date = None
        # first_iso = None
        all_prescriptions = {}
        success_drugs_count = 0
        total_count = 0
        discarded_count = self.row_start_data - 1
        for row in all_data[discarded_count:]:
            required_cols_in_null = [col for col in required_cols
                                     if not row[col["position"]]]
            if required_cols_in_null:
                discarded_count += 1
                continue
            total_count += 1
            # print("data_row \t", data_row)
            self.last_missing_row = None
            # is_same_date = False
            uuid = str(uuid_lib.uuid4())

            def generic_match_row(av_data, c_data):
                c_name = c_data["name"]
                el_id, orig_val = self.generic_match(c_data, av_data)
                av_data[f"{c_name}_id"] = el_id
                if not el_id:
                    err = f"No se encontró el {c_name}"
                    name_col = c_data["unique_field"].get("name_column")
                    self.append_missing_field(
                        row, name_col, orig_val, err, drug_uuid=uuid)

                return av_data

            available_data = {
                "data_file_id": self.data_file_id,
                "row_seq": int(row[0]),
                "uuid": uuid
            }

            available_data, some_date = self.complement_available_data(
                available_data, row)

            for built_col in built_cols:
                origin_values = []
                for origin_col in built_col["origin_cols"]:
                    origin_values.append(row[origin_col["position"]])
                concat_char = built_col.get("t_value", "")
                built_value = concat_char.join(origin_values)
                available_data[built_col["name"]] = built_value

            for divided_col in divided_cols:
                divided_char = divided_col.get("t_value")
                if not divided_char:
                    continue
                origin_value = row[divided_col["position"]]
                divided_values = origin_value.split(divided_char)
                destiny_cols = divided_col["destiny_cols"]
                for i, divided_value in enumerate(divided_values, start=1):
                    destiny_col = destiny_cols[i - 1]
                    available_data[destiny_col["name"]] = divided_value

            for global_col in global_cols:
                available_data[global_col["name"]] = global_col["t_value"]

            for tab_col in tab_cols:
                available_data[tab_col["name"]] = self.sheet_name

            for file_name_col in file_name_cols:
                available_data[file_name_col["name"]] = file_name

            for ceil_col in ceil_cols:
                available_data[ceil_col["name"]] = ceil_col["final_value"]

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

            cat_container = self.catalogs.get("container")
            available_data = generic_match_row(available_data, cat_container)

            folio_document = available_data.get("folio_document")
            folio_ocamis = "%s-%s-%s-%s" % (
                self.agency_id, iso_date[0], iso_date[1], folio_document)

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

                for cat_name, cat_data in self.catalogs.items():
                    if cat_name in ["container", "delegation"]:
                        continue
                    available_data = generic_match_row(available_data, cat_data)

                # clave_clues = available_data.pop(
                #     unique_clues.get("name"), None)
                # clues_id = self.clues_match(clave_clues)
                # available_data["clues_id"] = clues_id
                # if not clues_id and unique_clues:
                #     error = "No se encontró la CLUES"
                #     self.append_missing_field(
                #         row, unique_clues["name_column"], clave_clues,
                #         error, drug_uuid=uuid)
                clues_id = available_data.get("clues_id")
                delegation_id, delegation_error = self.delegation_match(
                    available_data, clues_id)

                if delegation_error:
                    self.append_missing_row(row, delegation_error)
                    continue
                available_data["delegation_id"] = delegation_id

                all_prescriptions[folio_ocamis] = available_data

            current_drug_data = []
            for drug_field in self.model_fields["drug"]:
                value = available_data.pop(drug_field, None)
                if value is None:
                    value = locals().get(drug_field)
                # value = available_data.get(drug_field, locals().get(drug_field))
                current_drug_data.append(value)
            csv_buffer["drug"].writerow(current_drug_data)
            success_drugs_count += 1
            # if len(all_prescriptions) > self.sample_size:
            #     break
        print("PASO 5")
        final_request_id = self.context.aws_request_id
        report_errors = self.build_report()
        report_errors["prescription_count"] = len(all_prescriptions)
        report_errors["drug_count"] = success_drugs_count
        report_errors["total_count"] = total_count
        report_errors["discarded_count"] = discarded_count
        print("PASO 6  -- LLEGO AL FINAL DE TODO")
        if self.is_prepare:
            print("PASO 7, en prepare")
            result_data = {
                "result": {
                    "final_paths": None,
                    "report_errors": report_errors,
                    "is_prepare": True
                },
                "request_id": final_request_id
            }
            return json.dumps(result_data)

        csv_buffer["missing_field"].writerows(self.all_missing_fields)
        csv_buffer["missing_row"].writerows(self.all_missing_rows)

        for curr_prescription in all_prescriptions.values():
            current_prescription_data = []
            # curr_prescription = all_prescriptions.get(folio)
            for field_name in self.model_fields["prescription"]:
                value = curr_prescription.get(field_name)
                current_prescription_data.append(value)
            csv_buffer["prescription"].writerow(current_prescription_data)

        bucket_name = self.s3.get("bucket_name")
        aws_location = self.s3.get("aws_location")

        all_final_paths = []

        for elem_list in self.editable_models:
            only_name = self.final_path.replace("NEW_ELEM_NAME", elem_list['name'])
            all_final_paths.append({
                "name": elem_list["name"],
                "path": only_name,
            })
            s3_client.put_object(
                Body=csv_files[elem_list["name"]].getvalue(),
                Bucket=bucket_name,
                Key=f"{aws_location}/{only_name}",
                ContentType="text/csv",
                ACL="public-read",
            )
            # self.send_csv_to_db(final_path, elem_list)

        result_data = {
            "result": {
                "decode": self.decode,
                "final_paths": all_final_paths,
                "report_errors": report_errors,
            },
            "request_id": final_request_id
        }
        return json.dumps(result_data)

    def get_json_file(self, file_name):
        aws_access_key_id = self.s3["aws_access_key_id"]
        aws_secret_access_key = self.s3["aws_secret_access_key"]
        bucket_name = self.s3["bucket_name"]
        aws_location = self.s3["aws_location"]

        # dev_resource = boto3.resource(
        #     's3', aws_access_key_id=aws_access_key_id,
        #     aws_secret_access_key=aws_secret_access_key)
        # content_object = dev_resource.Object(
        #     bucket_name=bucket_name,
        #     key=f"{aws_location}/{file_name}"
        # )
        # streaming_body_1 = content_object.get()['Body']
        # object_final = io.BytesIO(streaming_body_1.read())
        # return json.loads(object_final.read().decode('utf-8'))
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
        self.decode = self.obtain_decode(sample)
        # self.file_control.decode = decode
        # self.file_control.save()

        if self.decode == "unknown":
            error = "No se pudo decodificar el archivo"
            return [], [error], None

        # for row_seq, row in enumerate(data_rows[begin+1:], start=begin+1):
        for row_seq, row in enumerate(data_rows, start=1):
            # print("Row: %s" % row_seq)
            self.last_missing_row = None
            if self.is_prepare:
                row_data = [col.replace('\r\n', '').strip() for col in row]
            else:
                row_decode = row.decode(self.decode) if self.decode != "str" else str(row)
                # .replace('\r\n', '')
                row_data = row_decode.replace('\r\n', '').split(self.delimiter)
            current_count = len(row_data)
            row_data.insert(0, str(row_seq))
            if current_count == self.columns_count:
                structured_data.append(row_data)
            else:
                error = "Conteo distinto de Columnas; %s de %s" % (
                    current_count, self.columns_count)
                self.append_missing_row(row_data, error)

        return structured_data

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

    def complement_available_data(self, available_data, row):
        import re
        from datetime import datetime, timedelta
        some_date = None
        uuid = available_data.get("uuid")
        fields_with_name = [field for field in self.existing_fields
                            if field["name"] and field["position"]]
        for field in fields_with_name:
            error = None
            value = row[field["position"]]
            try:
                if field["data_type"] == "Datetime":  # and not is_same_date:
                    if value == self.last_date and value:
                        value = self.last_date_formatted
                    elif self.string_date == "EXCEL":
                        self.last_date = value
                        days = int(value)
                        seconds = (value - days) * 86400
                        seconds = round(seconds)
                        value = datetime(1899, 12, 30) + timedelta(days=days, seconds=seconds)
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
            regex_format = field.get("regex_format")
            if regex_format:
                if not re.match(regex_format, value):
                    error = "No se pudo validar con el formato %s" % regex_format
            if error:
                self.append_missing_field(
                    row, field["name_column"], value, error=error, drug_uuid=uuid)
                value = None
            available_data[field["name"]] = value
        return available_data, some_date

    # def medicine_match(self, available_data):
    #     cat_container = self.catalogs["container"]
    #     unique_field = cat_container.get("unique_field")
    #     if unique_field:
    #         new_key2 = available_data[unique_field].replace(".", "")
    #         available_data[unique_field] = new_key2
    #         curr_container = self.cats["container"].get(new_key2)
    #         # available_data["container_id"] = curr_container
    #         return curr_container, available_data[unique_field]
    #     return None, None

    def generic_match(self, cat_data, available_data):
        cat_name = cat_data["name"]
        if cat_name == "clues" and self.global_clues_id:
            return self.global_clues_id, None
        unique_field = cat_data.get("unique_field")
        if unique_field:
            params = cat_data.get("params", {})
            id_field = params.get("id", "id")
            init_value = available_data[unique_field.get("name")]
            if cat_name == "container":
                init_value = init_value.replace(".", "")
            # available_data[unique_field] = unique_field
            complete_values = self.cats[cat_name].get(init_value)
            final_value = complete_values.get(id_field) \
                if complete_values else None
            # available_data["container_id"] = final_value
            if not final_value and not params.get("only_unique"):
                final_value = self.append_catalog_row(cat_name, available_data)
            if not final_value:
                print(f"No se encontró init: {init_value} en {cat_name} \n "
                      f"unique_field: {unique_field}\n")
            return final_value, init_value
        else:
            print("No se encontró unique_field", cat_name)
        # elif not cat_data.get("only_unique"):
        #     return None, None
        #     # return self.append_catalog_row(cat_name, available_data), None
        return None, None

    def clues_match(self, clave_clues):
        if self.global_clues_id:
            return self.global_clues_id
        clues = None
        catalog_clues = self.catalogs["clues"]
        if clave_clues and catalog_clues:
            try:
                clues = self.cats["clues"].get(clave_clues)
            except KeyError:
                pass
        return clues

    def delegation_match(self, available_data, clues_id):
        delegation_name = available_data.pop("delegation_name", None)
        delegation = None
        delegation_error = None
        if self.global_delegation_id:
            delegation = self.global_delegation_id
        elif delegation_name:
            delegation_name = text_normalizer(delegation_name)
            try:
                delegation_cat = self.cats["delegation"][delegation_name]
                delegation = delegation_cat["id"]
            except Exception:
                delegation_error = f"No se encontró la delegación;" \
                                   f" {delegation_name}"
            is_failed = delegation_name in self.failed_delegations
            if not is_failed and not delegation and clues_id and self.total_tries < 20:
                delegation, delegation_error = self.create_delegation(
                    clues_id, delegation, delegation_error, delegation_name)
        return delegation, delegation_error

    def create_delegation(self, clues_id, delegation, delegation_error, delegation_name):
        data_query = json.dumps({
            "special_function": {
                "delegation_name": delegation_name,
                "clues_id": clues_id,
                "institution_id": self.institution_id
            }
        })
        response_create = requests.post(
            self.webhook_url, data=data_query, headers=request_headers)
        try:
            # RICK 18: No entiendo por qué se decodifica el contenido de la respuesta
            content = response_create.content
            # if self.decode == 'str':
            #    content = str(content)
            # else:
            content = content.decode(self.decode)
            content = json.loads(content)
            [data_result, delegation_error] = content
            if data_result:
                new_name = data_result["name"]
                self.cats["delegation"][new_name] = data_result
                # self.catalog_delegation[new_name] = data_result
                delegation = content["id"]
            else:
                self.failed_delegations.append(delegation_name)
        except Exception as e:
            self.total_tries += 1
            print("NO SE PUDO LEER", e)
            delegation_error = f"Hubo un error al crear la delegación; " \
                               f"{delegation_name}, error: {e}"
        # delegation, delegation_error = self.create_delegation(
        #     delegation_name, clues_id)
        return delegation, delegation_error

    def obtain_decode(self, sample):
        if self.decode:
            return self.decode

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

    def append_missing_row(self, row_data, error=None, drug_id=None):
        if self.last_missing_row:
            if error:
                # print(self.all_missing_rows)
                self.last_missing_row[-2] = False
                self.all_missing_rows[-1][-1] = error
            return self.all_missing_rows[-1][0]
        last_revised = self.last_revised
        inserted = not bool(error)
        inserted = False
        # row_seq = int(row_data[0])
        # original_data = row_data[1:]
        original_data = row_data
        missing_data = []
        uuid = str(uuid_lib.uuid4())
        data_file_id = self.data_file_id
        for field_name in self.model_fields["missing_row"]:
            value = locals().get(field_name)
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
        # print("error: %s" % error)
        for field_name in self.model_fields["missing_field"]:
            value = locals().get(field_name)
            missing_field.append(value)
        self.all_missing_fields.append(missing_field)

    def append_catalog_row(self, cat_name, available_data):
        uuid = str(uuid_lib.uuid4())
        inserted = False
        last_revised = self.last_revised
        is_aggregate = False
        institution_id = self.institution_id
        delegation_id = self.global_delegation_id
        new_row = []
        row_data = {}
        for field_name in self.model_fields[cat_name]:
            value = available_data.get(field_name, locals().get(field_name))
            new_row.append(value)
            row_data[field_name] = value
        self.new_cat_rows[cat_name].append(new_row)
        self.cats[cat_name][uuid] = row_data
        return uuid

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
                    print("error", e)
                    [error_type, error_detail] = [error, error]
                if error_type in row_errors:
                    row_errors[error_type]["count"] += 1
                    if error_detail in row_errors[error_type]:
                        row_errors[error_type][error_detail]["count"] += 1
                        example_count = len(
                            row_errors[error_type][error_detail]["examples"])
                        if example_count < 4:
                            row_errors[error_type][error_detail]["examples"].append(
                                missing_row)
                    elif len(row_errors[error_type]) < 20:
                        row_errors[error_type][error_detail] = {
                            "count": 1, "examples": [missing_row]}
                elif error_types_count < 40:
                    row_errors[error_type] = {
                        "count": 1,
                        error_detail: {
                            "count": 1, "examples": [missing_row]}
                    }
                    error_types_count += 1
            row_errors = sorted(row_errors.items(), key=lambda x: x[1], reverse=True)
            row_errors = row_errors[:50]
            report_data["row_errors"] = row_errors
            if len(row_errors) > 50:
                report_data["general_errors"] += \
                    "Se encontraron más de 50 tipos de errores en las filas"

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

        if not report_data.get("missing_rows") and not report_data.get("missing_fields"):
            report_data["general_errors"] = "No se encontraron errores"
        return report_data
