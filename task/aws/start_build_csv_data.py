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
        return None, error

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
        return None, error
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
    init_data = event["init_data"]
    init_data["s3"] = event["s3"]
    init_data["webhook_url"] = event.get("webhook_url")
    match_aws = MatchAws(init_data, context)

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
        for key, value in init_data.items():
            setattr(self, key, value)
        self.data_file_id = init_data["data_file_id"]
        # self.file_control_id = init_data["file_control_id"]
        self.global_clues_id = init_data["global_clues_id"]
        self.entity_id = init_data["entity_id"]
        self.institution_id = init_data["institution_id"]
        # self.global_state_id = init_data["global_state_id"]
        self.global_delegation_id = init_data["global_delegation_id"]
        self.decode = init_data["decode"]
        self.final_path = init_data["final_path"]
        self.row_start_data = init_data["row_start_data"]
        self.delimiter = init_data["delimiter"]
        self.columns_count = init_data["columns_count"]
        self.final_lists = init_data["final_lists"]
        self.model_fields = init_data["model_fields"]
        self.existing_fields = init_data["existing_fields"]
        self.catalog_clues_by_id = init_data["catalog_clues_by_id"]
        self.catalog_delegation = init_data["catalog_delegation"]
        self.catalog_container = init_data["catalog_container"]
        self.webhook_url = init_data.get("webhook_url")

        self.string_date = init_data["string_date"]
        self.unique_clues = init_data["unique_clues"]
        self.failed_delegations = []

        self.last_missing_row = None
        self.all_missing_rows = []
        self.all_missing_fields = []
        self.s3 = init_data["s3"]
        self.context = context
        self.total_tries = 1

    def build_csv_to_data(self, complete_file, s3_client):
        csv_buffer = { }
        csv_files = { }
        for elem in self.final_lists:
            csv_files[elem["name"]] = io.StringIO()
            csv_buffer[elem["name"]] = csv.writer(
                csv_files[elem["name"]], delimiter=self.delimiter)

        data_rows = complete_file.readlines()

        all_data = self.divide_rows(data_rows)

        # last_date = None
        # iso_date = None
        # first_iso = None
        all_prescriptions = { }
        for row in all_data:
            # print("data_row \t", data_row)
            self.last_missing_row = None
            # is_same_date = False
            available_data = {
                "data_file_id": self.data_file_id,
                "row_seq": row[0],
                "uuid": uuid_lib.uuid4()
            }
            available_data, some_date = self.complement_available_data(
                available_data, row)

            if not some_date:
                error = "No se pudo convertir ninguna fecha"
                self.all_missing_rows[-1][-1] = error
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
                self.append_missing_row(row[0], row[1:], error)
                continue
            delivered = available_data.get("delivered_id")

            available_data = self.medicine_match(available_data)

            folio_document = available_data.get("folio_document")
            folio_ocamis = "%s-%s-%s-%s" % (
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
                uuid_folio = uuid_lib.uuid4()
                available_data["uuid_folio"] = uuid_folio
                available_data["prescription_id"] = uuid_folio
                available_data["delivered_final_id"] = delivered
                available_data["folio_ocamis"] = folio_ocamis
                available_data["folio_document"] = folio_document
                available_data["all_delivered"] = [delivered]

                clues_id = self.clues_match(available_data, self.unique_clues)
                available_data["clues_id"] = clues_id
                delegation_name = available_data.get("delegation_name")
                if not delegation_name == "AGUASCALIENTES":
                    continue

                delegation_id, delegation_error = self.delegation_match(
                    available_data, clues_id)
                if not delegation_id:
                    self.append_missing_row(row[0], row[1:], delegation_error)
                    continue
                available_data["delegation_id"] = delegation_id

                all_prescriptions[folio_ocamis] = available_data

            current_drug_data = []
            for drug_field in self.model_fields["drug"]:
                value = available_data.pop(drug_field, None)
                if not value:
                    value = locals().get(drug_field)
                # value = available_data.get(drug_field, locals().get(drug_field))

                current_drug_data.append(value)
            csv_buffer["drug"].writerow(current_drug_data)

            # IMPORTANTE: Falta un proceso para los siguientes campos:
            # doctor = None
            # area = None
            # diagnosis = None

            # if len(all_prescriptions) > self.sample_size:
            #     break

        for curr_prescription in all_prescriptions.values():
            current_prescription_data = []
            # curr_prescription = all_prescriptions.get(folio)
            for field_name in self.model_fields["prescription"]:
                value = curr_prescription.get(field_name, locals().get(field_name))
                current_prescription_data.append(value)
            csv_buffer["prescription"].writerow(current_prescription_data)

        bucket_name = self.s3.get("bucket_name")
        aws_location = self.s3.get("aws_location")

        all_final_paths = []

        for elem_list in self.final_lists:
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
            },
            "request_id": self.context.aws_request_id
        }
        return json.dumps(result_data)

    def divide_rows(self, data_rows):
        structured_data = []
        sample = data_rows[:20]
        self.decode = self.obtain_decode(sample)
        # self.file_control.decode = decode
        # self.file_control.save()

        if self.decode == "unknown":
            error = "No se pudo decodificar el archivo"
            return [], [error], None

        begin = self.row_start_data

        for row_seq, row in enumerate(data_rows[begin - 1:], start=begin):
            # print("Row: %s" % row_seq)
            self.last_missing_row = None
            row_decode = row.decode(self.decode) if self.decode != "str" else str(row)
            # .replace('\r\n', '')
            row_data = row_decode.replace('\r\n', '').split(self.delimiter)
            if len(row_data) == self.columns_count:
                row_data.insert(0, str(row_seq))
                structured_data.append(row_data)
            else:
                errors = ["Conteo distinto de Columnas: %s de %s" % (
                    len(row_data), self.columns_count)]
                self.append_missing_row(row_seq, row, errors)

        return structured_data

    def complement_available_data(self, available_data, row):
        from datetime import datetime
        some_date = None
        uuid = available_data.get("uuid")
        for field in self.existing_fields:
            value = row[field["position"]]
            if field["data_type"] == "Datetime":  # and not is_same_date:
                # if value == last_date:
                #     is_same_date = True
                try:
                    value = datetime.strptime(value, self.string_date)
                    if not some_date:
                        some_date = value
                        # last_date = value
                except ValueError:
                    error = "No se pudo convertir la fecha"
                    self.append_missing_field(
                        row, field["column"], value, error=error, drug_uuid=uuid)
                    value = None
            elif field["data_type"] == "Integer":
                try:
                    value = int(value)
                except ValueError:
                    error = "No se pudo convertir a número entero"
                    self.append_missing_field(
                        row, field["column"], value, error=error, drug_uuid=uuid)
                    value = None
            elif field["data_type"] == "Float":
                try:
                    value = float(value)
                except ValueError:
                    error = "No se pudo convertir a número decimal"
                    self.append_missing_field(
                        row, field["column"], value, error=error, drug_uuid=uuid)
                    value = None
            available_data[field["name"]] = value
        return available_data, some_date

    def medicine_match(self, available_data):
        if available_data.get("key2"):
            new_key2 = available_data["key2"].replace(".", "")
            available_data["key2"] = new_key2
            curr_container = self.catalog_container.get(new_key2)
            available_data["container_id"] = curr_container
        return available_data

    def clues_match(self, available_data, unique_clues):
        clues = None
        clave_clues = available_data.pop(unique_clues.get("name"), None)
        if self.global_clues_id:
            clues = self.global_clues_id
        elif clave_clues and self.catalog_clues_by_id:
            try:
                clues = self.catalog_clues_by_id.get(clave_clues)
            except KeyError:
                pass
        return clues

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

    def append_missing_row(
            self, row_seq, original_data, error=None, drug_id=None):
        if self.last_missing_row:
            self.all_missing_rows[-1][-1] = error
            return self.all_missing_rows[-1][0]
        missing_data = []
        uuid = str(uuid_lib.uuid4())
        data_file_ic = self.data_file_id
        for field_name in self.model_fields["missing_row"]:
            value = locals().get(field_name)
            missing_data.append(value)
        self.last_missing_row = missing_data
        self.all_missing_rows.append(missing_data)
        return uuid

    def append_missing_field(
            self, row, name_column_id, original_value, error, drug_uuid=None):
        missing_row_id = self.append_missing_row(row[0], row, drug_id=drug_uuid)
        missing_field = []
        uuid = str(uuid_lib.uuid4())
        # if name_column:
        #     name_column = name_column.id
        # print("error: %s" % error)
        for field_name in self.model_fields["missing_field"]:
            value = locals().get(field_name)
            missing_field.append(value)
        self.all_missing_fields.append(missing_field)

    def delegation_match(self, available_data, clues_id):
        delegation_name = available_data.pop("delegation_name", None)
        delegation = None
        delegation_error = None
        if self.global_delegation_id:
            delegation = self.global_delegation_id
        elif delegation_name:
            delegation_name = text_normalizer(delegation_name)
            try:
                delegation_cat = self.catalog_delegation[delegation_name]
                delegation = delegation_cat["id"]
            except Exception as e:
                delegation_error = f"No se encontró la delegación" \
                                   f" {delegation_name} ({e})"
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
            content = str(content)
            # else:
            #     content = content.decode(self.decode)
            content = json.loads(content)
            [data_result, delegation_error] = content
            if data_result:
                new_name = data_result["name"]
                self.catalog_delegation[new_name] = data_result
                delegation = content["id"]
            else:
                self.failed_delegations.append(delegation_name)
        except Exception as e:
            self.total_tries += 1
            print("NO SE PUDO LEER", e)
            delegation_error = "ESTAMOS EXPERIMENTANDO CREAR"
        # delegation, delegation_error = self.create_delegation(
        #     delegation_name, clues_id)
        return delegation, delegation_error
