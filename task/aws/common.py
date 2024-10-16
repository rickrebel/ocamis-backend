import boto3
import json
import requests
import math
request_headers = {"Content-Type": "application/json"}


class ValueProcessError(Exception):
    def __init__(self, message, value=None, error_msg=None):
        final_msg = message
        if error_msg:
            final_msg = f"{message}; error detallado: {error_msg}"
        super().__init__(final_msg)
        self.value = value
        self.message = final_msg


class EarlyResult(Exception):

    def __init__(self, result, delivered, warning=None):
        self.result = result
        self.delivered = delivered
        self.warning = None
        if warning:
            self.warning = f"warning: {warning}"
        super().__init__("Early result")


class SendResultToWebhook:

    def __init__(self, event, json_result):
        self.webhook_url = event["webhook_url"]
        self.s3 = event.get("s3")
        self.json_result = json_result
        self.sum_time = 0
        self.current_time = 2

    def send_to_webhook(self):
        import time
        response_data = requests.post(
            self.webhook_url, data=self.json_result, headers=request_headers)
        # print("response_data", response_data)
        try:
            # response_json = response_data.json()
            # print("response_json", response_json)
            text_response = response_data.text
            # content = response_data.content
            # content_str = content.decode("utf-8")
            status_code = response_data.status_code
            if text_response == "error":
                self.save_error_task("ocamis")
            elif status_code != 200:
                self.current_time *= 2
                self.sum_time += self.current_time
                # print("ERROR EN WEBHOOK")
                # print("content_str", text_response)
                if self.sum_time < 120:
                    time.sleep(self.current_time)
                    self.send_to_webhook()
                else:
                    self.save_error_task("time_response")

        except Exception as e:
            print("error_basic", e)
            self.save_error_task("webhook")

    def save_error_task(self, type_error):
        result_data = json.loads(self.json_result)
        result_data["type_error"] = type_error
        # lambda_utils = BotoUtils(self.s3, service="lambda")
        # lambda_utils.s3_client.invoke(
        #     FunctionName='retry_task',
        #     InvocationType='Event',
        #     LogType='Tail',
        #     Payload=json.dumps(result_data)
        # )
        s3_utils = BotoUtils(self.s3)
        request_id = result_data.get("request_id")
        file_name = f"aws_errors/{request_id}.json"
        s3_utils.save_json_file(result_data, file_name)


def send_simple_response(event, context, errors=None, result=None):
    if not errors:
        errors = []
    if not result:
        result = {}
    else:
        pass
        # print("result:", result)
    #     try:
    #         json.dumps(result)
    #         print("serializable result ok")
    #     except Exception as e:
    #         print("error serializable result", e)
    result["success"] = bool(not errors)
    result["errors"] = errors
    # try:
    #     json.dumps(errors)
    #     print("serializable errors ok")
    # except Exception as e:
    #     print("error serializable errors", e)
    result_data = {
        "result": result,
        "request_id": context.aws_request_id,
        "aws_function_name": context.function_name,
        "function_name": event.get("function_name"),
    }
    json_result = json.dumps(result_data)
    send_result = SendResultToWebhook(event, json_result)
    send_result.send_to_webhook()

    return {
        'statusCode': 200,
        'body': json_result
    }


def send_simple_response_2(event, context, result):
    result["success"] = bool(not result["errors"])
    result_data = {
        "result": result,
        "request_id": context.aws_request_id,
        "aws_function_name": context.function_name,
        "function_name": event.get("function_name"),
    }
    json_result = json.dumps(result_data)
    send_result = SendResultToWebhook(event, json_result)
    send_result.send_to_webhook()

    return {
        'statusCode': 200,
        'body': json_result
    }


def create_connection(db_config):
    import psycopg2
    connection = psycopg2.connect(
        database=db_config.get("NAME"),
        user=db_config.get("USER"),
        password=db_config.get("PASSWORD"),
        host=db_config.get("HOST"),
        port=db_config.get("PORT"))
    return connection


class BotoUtils:

    def __init__(self, s3=None, service="s3"):
        import os

        self.bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME', 'cdn-desabasto')
        self.aws_location = os.getenv('AWS_LOCATION', 'data_files')
        if s3:
            self.s3_client = boto3.client(
                service, aws_access_key_id=s3["aws_access_key_id"],
                aws_secret_access_key=s3["aws_secret_access_key"])

            self.dev_resource = boto3.resource(
                service, aws_access_key_id=s3["aws_access_key_id"],
                aws_secret_access_key=s3["aws_secret_access_key"])
        else:
            self.s3_client = boto3.client(service)
            self.dev_resource = boto3.resource(service)
        region = os.getenv("AWS_S3_REGION_NAME", "us-west-2")
        self.absolute_path = f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
        self.errors = []

    def get_streaming_body(self, file, read=False):
        content_object = self.dev_resource.Object(
            bucket_name=self.bucket_name,
            key=f"{self.aws_location}/{file}")
        streaming_body = content_object.get()['Body']
        if content_object.content_encoding == "gzip":
            import gzip
            streaming_body = gzip.GzipFile(fileobj=streaming_body)
        if read:
            streaming_body = streaming_body.read()
        return streaming_body

    def get_object_csv(self, file, delimiter="|"):
        import csv
        from io import StringIO
        object_final = self.get_streaming_body(file, read=True)
        object_final = object_final.decode("utf-8")
        string_object = StringIO(object_final)
        csv_content = csv.reader(string_object, delimiter=delimiter)
        return csv_content

    def get_object_bytes(self, file):
        from io import BytesIO
        object_final = self.get_streaming_body(file, read=True)
        object_final = BytesIO(object_final)
        return object_final

    def get_json_file(self, file_name, decode="utf-8"):
        import json

        obj = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=f"{self.aws_location}/{file_name}")

        return json.loads(obj['Body'].read().decode(decode))

    def _compress_content(self, content, is_raw=False):
        from gzip import GzipFile
        from io import BytesIO
        if not is_raw:
            content.seek(0)

        # if is_gzip:
        #     if len(body) < 5000:
        #         is_gzip = False

        gz_buffer = BytesIO()
        read_content = content.encode("utf-8") if is_raw else content.read()
        # size = len(read_content)
        # print("-" * 50)
        # print("is_raw", is_raw)
        # print("size", size)
        # if size < 5000:
        #     print("El archivo es muy pequeño para comprimir")
        #     raise ValueProcessError("El archivo es muy pequeño para comprimir")

        with GzipFile(mode='wb', fileobj=gz_buffer, mtime=0.0) as gz_file:
            gz_file.write(read_content)
        gz_buffer.seek(0)
        return gz_buffer.getvalue()

    def save_file_in_aws(
            self, body, final_name, content_type="text/csv",
            storage_class="STANDARD", is_gzip=False, is_raw=False):

        final_object = {
            "Bucket": self.bucket_name,
            "Key": f"{self.aws_location}/{final_name}",
            "ACL": "public-read",
            "StorageClass": storage_class
        }
        if content_type:
            final_object["ContentType"] = content_type

        if is_gzip:
            try:
                body = self._compress_content(body, is_raw)
                final_object["ContentEncoding"] = "gzip"
            except Exception as e:
                pass

        final_object["Body"] = body
        success_file = self.s3_client.put_object(**final_object)
        if not success_file:
            self.errors.append(f"Error al guardar el archivo {final_name}")
        return success_file

    def save_csv_in_aws(
            self, buffer, final_name, storage_class="STANDARD", is_gzip=False):
        object_file = buffer.getvalue()
        self.save_file_in_aws(
            object_file, final_name, content_type="text/csv",
            storage_class=storage_class, is_gzip=is_gzip, is_raw=True)

    def save_json_file(self, json_object, final_name):
        import json
        object_file = json.dumps(json_object)
        self.save_file_in_aws(
            object_file, final_name, content_type="text/json")

    def move_and_gzip_file(
            self, path_origin, path_destiny, storage_class="STANDARD"):

        if path_origin.endswith(".csv") or path_origin.endswith(".txt"):
            file_object = self.get_object_bytes(path_origin)
            self.save_file_in_aws(
                file_object, path_destiny, storage_class=storage_class,
                is_gzip=True)
        else:
            self.change_storage_class(
                path_origin, storage_class=storage_class,
                path_destiny=path_destiny)

    def change_storage_class(
        self,
        path_origin,
        storage_class="STANDARD",
        acl="public-read",
        path_destiny=None
    ):
        key_origin = f"{self.aws_location}/{path_origin}"
        key_destiny = key_origin
        if path_destiny:
            key_destiny = f"{self.aws_location}/{path_destiny}"
        final_object = {
            "CopySource": {
                "Bucket": self.bucket_name,
                "Key": key_origin
            },
            "Bucket": self.bucket_name,
            "Key": key_destiny,
            "ExtraArgs": {
                "StorageClass": storage_class,
                "ACL": acl
            }
        }
        self.s3_client.copy(**final_object)
        # if path_destiny and path_origin != path_destiny:
        #     self.delete_file(path_origin)

    def delete_file(self, file_name):
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.aws_location}/{file_name}"
        )

    def check_exist(self, file_name):
        try:
            self.dev_resource.Object(
                bucket_name=self.bucket_name,
                key=f"{self.aws_location}/{file_name}").load()
            return True
        except Exception as e:
            return False

    def get_full_path(self, file_name):
        return f"{self.absolute_path}/{self.aws_location}/{file_name}"


def calculate_delimiter(data):
    error_count = 0
    for row in data:
        try:
            if "|" in row:
                return "|"
        except Exception as e:
            error_count += 1
            if error_count > 3:
                print("row:\n", row)
                print("error", e)
                if "|" in row:
                    return "|"
    return ","


def obtain_decode(sample):
    sample_count = 0
    for row in sample:
        sample_count += 1
        if sample_count > 51:
            return 'str'
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


def decode_content(rows, decode):
    decoded_data = []
    for row in rows:
        content = str(row) if decode == 'str' else row.decode(decode)
        decoded_data.append(content)
    return decoded_data


def calculate_delivered_final(all_delivered, all_write=None):
    error = None
    if all_write:
        if len(all_write) > 1:
            error = f"Hay más de una clasificación de surtimiento;" \
                    f" {list(all_write)}"

    if len(all_delivered) == 1:
        return all_delivered.pop(), error
    if "partial" in all_delivered or "big_partial" in all_delivered:
        return "partial", error
    has_complete = "complete" in all_delivered
    has_over = "over_delivered" in all_delivered
    has_denied = "denied" in all_delivered or "big_denied" in all_delivered
    has_cancelled = "cancelled" in all_delivered
    if (has_complete or has_over) and (has_denied or has_cancelled):
        return "partial", error
    initial_list = all_delivered.copy()
    if "zero" in all_delivered:
        all_delivered.remove("zero")
    if has_over and has_complete:
        all_delivered.remove("complete")
    if has_denied and has_cancelled:
        if "denied" in all_delivered:
            all_delivered.remove("denied")
        if "big_denied" in all_delivered:
            all_delivered.remove("big_denied")
    if len(all_delivered) == 1:
        return next(iter(all_delivered)), error
    elif len(all_delivered) == 2:
        if "denied" in initial_list and "big_denied" in initial_list:
            return "denied", error
    error = f"No se puede determinar el status de entrega; {list(initial_list)}"
    return "unknown", error


class DeliveredCalculator:

    def __init__(self, global_delivered=None, available_deliveries=None):
        self.global_delivered = global_delivered
        self.available_deliveries = available_deliveries
        self.available_data = {}
        self.final_class = None
        self.class_med = None
        self.prescribed_amount = None
        self.delivered_amount = None
        self.is_cancelled = False

    # def calculate_delivered(self, available_data):
    def __call__(self, available_data):

        self.available_data = available_data

        self.class_med = self._get_and_normalize("clasif_assortment")
        class_presc = self._get_and_normalize("clasif_assortment_presc")
        self.final_class = self.class_med or class_presc
        self.is_cancelled = self.final_class == "CANCELADA"

        self.prescribed_amount = self.calc_main_quantity("prescribed_amount")
        self.delivered_amount = self.calc_main_quantity("delivered_amount")

        if self.global_delivered:
            return self.set_delivered(self.global_delivered)

        if self.prescribed_amount == self.delivered_amount:
            if self.is_cancelled:
                delivered = "cancelled"
            elif self.prescribed_amount == 0:
                delivered = "zero"
            else:
                delivered = "complete"
        elif not self.delivered_amount:
            if self.is_cancelled:
                delivered = "cancelled"
            else:
                delivered = "denied"
        elif self.delivered_amount < self.prescribed_amount:
            delivered = "partial"
        elif self.delivered_amount > self.prescribed_amount:
            delivered = "over_delivered"
        elif self.is_cancelled:
            delivered = "cancelled"
        else:
            raise ValueProcessError(
                "No se puede determinar el status de entrega")

        if self.prescribed_amount > 30:
            if delivered == "denied":
                delivered = "big_denied"
            elif delivered == "partial":
                delivered = "big_partial"

        return self.set_delivered(delivered)

    def calc_main_quantity(self, field):
        is_delivered = field == "delivered_amount"
        err_text = "entregada" if is_delivered else "prescrita"

        amount = self.available_data.get(field)

        if amount is None and is_delivered:
            amount = self._calc_delivered_with_opposite()

        if amount is not None:
            try:
                amount = int(amount)
            except ValueError:
                error = f"No se pudo convertir; la cantidad {err_text}"
                raise ValueProcessError(error, amount)

        if amount is None:
            if self.is_cancelled:
                self.set_default("prescribed_amount")
                self.set_default("delivered_amount")
                self.set_delivered("cancelled", True)
            elif self.global_delivered:
                pass
            elif is_delivered and self.final_class:
                self._calc_write_delivered()
            else:
                err = f"No se puede determinar el status; cantidad {err_text}"
                raise ValueProcessError(err, amount)
        elif amount > 30000:
            err = f"Existe una cantidad inusualmente alta; cantidad {err_text}"
            raise ValueProcessError(err, amount)
        elif amount < 0:
            err = f"Existe una cantidad negativa; cantidad {err_text}"
            raise ValueProcessError(err, amount)

        self.available_data[field] = amount
        return amount

    def _calc_write_delivered(self):
        amount = None
        real_class = self.available_deliveries[self.final_class]
        if real_class in ['cancelled', 'denied']:
            amount = 0
        elif real_class == 'complete':
            amount = self.prescribed_amount
        elif real_class == 'partial':
            if self.class_med:
                amount = int(math.floor(self.prescribed_amount / 2))
            else:
                amount = self.prescribed_amount
                real_class = 'forced_partial'
        if amount is not None:
            self.available_data["delivered_amount"] = amount
            self.set_delivered(real_class, True)
        else:
            raise ValueProcessError(
                f"No se pudo obtener la cantidad entregada; "
                f"de la clasificación {self.final_class}")

    def _get_and_normalize(self, field_name):
        if value := self.available_data.get(field_name):
            value = text_normalizer(value)
            if value not in self.available_deliveries:
                err = f"Clasificación de surtimiento no contemplada"
                raise ValueProcessError(err, value)
            return value
        return None

    def set_default(self, field_name):
        if self.available_data.get(field_name) is None:
            self.available_data[field_name] = 0

    def set_delivered(self, delivered, want_raise=False):
        warning = None
        if self.class_med:
            if delivered != self.available_deliveries[self.class_med]:
                warning = (f"El status escrito '{self.class_med}' no"
                           f" coincide con el status calculado: '{delivered}'")
        # FALLA
        if not self.prescribed_amount and self.global_delivered:
            pass
        elif self.prescribed_amount > 30:
            if delivered == "denied":
                delivered = "big_denied"
            elif delivered == "partial":
                delivered = "big_partial"
        self.available_data["delivered_id"] = delivered
        if want_raise or warning:
            raise EarlyResult(
                self.available_data, delivered, warning)
        return delivered, self.available_data

    def _calc_delivered_with_opposite(self):
        not_delivered_amount = self.available_data.get("not_delivered_amount")
        if not_delivered_amount is not None:
            try:
                not_delivered_amount = int(not_delivered_amount)
            except ValueError:
                error = (f"No se pudo convertir la cantidad 'no entregada'; "
                         f"{not_delivered_amount}")
                raise ValueProcessError(error, not_delivered_amount)
            return self.prescribed_amount - not_delivered_amount
        return None


def convert_to_str(x):
    undict = {
        'â€¦': '…', "â€ž": "„", 'â€“': '–', 'â€™': '’', "â€\x9d": "”",
        "â€š": "„", "â€°": "‰",
        'â€œ': '“', "â€”": '—', "Â\xad": " ", 'Ã©': "é", 'â‚¬': '€',
        "â€˜": "‘", 'Â£': "£", "Ã¢": "â", "Â©": "©", 'Ã£': "ã", "Ãº": 'ú',
        'Ã¤': 'ä', "â€¢": "•", 'Ã¡': 'á', 'Ã¼': 'ü', "Â¢": '¢', "Ã±": "ñ", "Ã‘": "Ñ",
        'Â½': 'Ž', 'Ã‰': 'É', 'Â¥': '¥', 'Ã§': 'ç', 'Ã´': '´', 'Â®': '®',
        'Â¦': '¦', "Ã¯": "ï", 'Ã¶': 'ö', 'Â´': "´", "Ëœ": "˜", 'Â»': '»',
        'Ã«': "ë", "Ã‡": "Ç", "Ã³": "ó", "Ãµ": "õ", "Ã®": "î", "Â¾": '¾',
        "Â¼": "¼", "Â°": "°", "Ã–": "Ö", "Ã¥": 'å', "Ã¨": "è", "Â¯": "¯",
        "Â¬": "¬", "Ã„": "Ä", "Â§": "§", "Ãœ": "Ì", "Â¤": "¤", "Â·": '·',
        "Â±": "±", "Ã²": "ò", "Ãƒ": "Ã", "ÃŸ": "ß", "Ã’": "Ò",
        "Â¡": "¡", "Ãª": "ê", "Â«": "«",
        "Ã\x8d": "Í", "Ã\x81": 'Á', "Ã\xad": "í", "Ã¦": "æ", "Â¿": "¿", "Ã¸": "ø",
        "Ã½": "ý", "Ã»": "û", "Ã¹": "ù", "Å½": "Ž", "Â¨": "¨", "Âµ": "µ",
        "Â²": "²", "Â³": "³", "Â¹": "¹", "â„¢": "™", "Ã“": "Ó"}
    for k, v in undict.items():
        x = x.replace(k, v)
    return x


def text_normalizer(text):
    import unidecode
    import re
    if not text:
        return ""
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.strip()
