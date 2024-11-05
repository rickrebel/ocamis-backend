import json
import io
import csv
import re
from task.aws.common import obtain_decode, ValueProcessError
from datetime import datetime, timedelta


class GetAllRows:

    def __init__(self, transform_class):
        self.transform_class = transform_class

        self.s3_utils = transform_class.s3_utils
        self.existing_fields = transform_class.existing_fields or []
        self.positioned_fields = [field for field in self.existing_fields
                                  if field["position"] is not None]

        global_transformations = transform_class.global_transformations or []
        self.fill_columns = "fill_columns" in global_transformations
        self.is_prepare = transform_class.is_prepare or False
        self.columns_count = transform_class.columns_count

        self.string_date = transform_class.string_date

        self.delimit = transform_class.delimiter or "|"
        self.sep = "\|" if self.delimit == "|" else self.delimit
        self.regex_fields = self.build_regex_and_dates()

    def __call__(self, file):

        file_type = "json" if self.is_prepare else "csv"
        complete_file = self.s3_utils.get_object_bytes(file)
        if self.is_prepare:
            complete_file = json.loads(complete_file.read())
            data_rows = complete_file.get("all_data", [])
            if len(data_rows) >= 198:
                tail_data = complete_file.get("tail_data", [])
                data_rows.extend(tail_data)
        else:
            data_rows = complete_file.readlines()
            # data_rows = complete_file
        return self.divide_rows(data_rows)

    def divide_rows(self, data_rows):
        import json

        sample = data_rows[:50]
        if not self.transform_class.decode:
            self.transform_class.decode = obtain_decode(sample)
        decoded = self.transform_class.decode
        if decoded == "latin-1":
            self.transform_class.decode_final = 'latin-1'

        if decoded == "unknown":
            raise ValueError("No se pudo decodificar el archivo")

        # for row_seq, row in enumerate(data_rows[begin+1:], start=begin+1):
        final_rows_with_cols = []
        for row_seq, row in enumerate(data_rows, start=1):
            self.transform_class.last_missing_row = None
            if self.is_prepare:
                row_final = [col.replace('\r\n', '').strip() for col in row]
                row_data = json.dumps(row_final).replace('\r\n', '')
            else:
                row_decode = row.decode(decoded) if decoded != "str" else str(row)
                # .replace('\r\n', '')
                row_data = row_decode.replace('\r\n', '')
                row_final = row_data.split(self.delimit)
                row_final = [col.strip() for col in row_final]
            current_count = len(row_final)

            if self.regex_fields and current_count > self.columns_count:
                row_final = self.special_division(row_data)
                current_count = len(row_final)

            if current_count == self.columns_count:
                row_final.insert(0, str(row_seq))
                final_rows_with_cols.append(row_final)
            elif self.fill_columns:
                row_final.insert(0, str(row_seq))
                row_final.extend([None] * (self.columns_count - current_count))
                final_rows_with_cols.append(row_final)
            else:
                error = "Conteo distinto de Columnas; %s de %s" % (
                    current_count, self.columns_count)
                row_data = [str(row_seq), row_data]
                self.transform_class.add_missing_row(row_data, error)

        return final_rows_with_cols

    def string_time_to_regex(self, string_time):
        conversion_map = {
            '%Y': r'\d{4}',
            '%m': r'\d{2}',
            '%d': r'\d{2}',
            '%H': r'\d{2}',
            '%M': r'\d{2}',
            '%S': r'\d{2}',
            '%f': r'\d{3,6}',
            ' ': r'\s',
            '-': r'-',
            ':': r':',
            '.': r'.',
        }

        regex_pattern = string_time
        for key, value in conversion_map.items():
            regex_pattern = regex_pattern.replace(key, value)
        return f"{self.sep}?({regex_pattern}){self.sep}?"

    def build_regex_and_dates(self):
        sep_fields = [field for field in self.existing_fields
                      if field.get("same_separator")]
        if len(sep_fields) == 0:
            return []
        regex_fields = []
        for field in self.existing_fields:
            regex_string = None
            if field["regex_format"] and len(field["regex_format"]) > 10:
                regex_string = field["regex_format"][1:-1]
                regex_string = f"{self.sep}?({regex_string}){self.sep}?"
            simple_regex = field.get("simple_regex")
            if simple_regex is True:
                regex_string = f"{self.sep}(){self.sep}"
            elif simple_regex is not None:
                if "(" in simple_regex:
                    regex_string = f"{self.sep}{simple_regex}{self.sep}"
                else:
                    regex_string = f"{self.sep}({simple_regex}){self.sep}"
            elif field["data_type"] == "Datetime":
                if self.string_date == "MANY":
                    date_regex = field.get("format_date")
                    if ";" in date_regex:
                        pass
                    elif date_regex:
                        regex_string = self.string_time_to_regex(date_regex)
                    else:
                        regex_string = False
                elif self.string_date != "EXCEL" and ";" not in self.string_date:
                    regex_string = self.string_time_to_regex(self.string_date)
            if regex_string:
                field["regex"] = regex_string
                regex_fields.append(field)
        if regex_fields:
            regex_fields.append({
                "position": self.positioned_fields[-1]["position"] + 1,
                "regex": f"$"
            })
        return regex_fields

    def special_division(self, row_data):
        fragments = []

        def build_blocks(re_field, remain_data):
            # print("remain_data", remain_data)
            regex = re_field["regex"]
            # print("regex", regex)
            results = re.split(regex, remain_data, 1)
            if len(results) == 1:
                if remain_data.startswith(self.delimit):
                    results = ["", "", remain_data[1:]]
                else:
                    results.extend([None, ""])
            elif len(results) == 2:
                results.append("")
            return results, re_field["position"]

        prev_pos = None
        next_pos = 1
        remain_block = row_data
        for idx, regex_field in enumerate(self.regex_fields):
            prev_pos = next_pos if prev_pos is not None else 0
            res, next_pos = build_blocks(regex_field, remain_block)

            try:
                [current_block, same, remain_block] = res
            except Exception as e:
                # print("Error", e)
                print("res", res)
                # print("row_data", row_data)
                print("regex_field", regex_field)
                print("remain_block", remain_block)
                raise e
            block_fields = [field for field in self.positioned_fields
                            if prev_pos < field["position"] < next_pos]
            len_block_fields = len(block_fields)
            if len_block_fields == 0:
                if same is not None:
                    fragments.append(same)
                continue
            position_separator = None
            for idx_block, block_field in enumerate(block_fields):
                same_separator = block_field.get("same_separator")
                if same_separator:
                    if position_separator is None:
                        position_separator = idx_block
                    else:
                        return row_data
            # fields_with_separator = [field for field in block_fields
            #                          if field.get("clean_function") == "same_separator"]
            # some_has_separator = any(fields_with_separator)
            # len_with_separator = len(fields_with_separator)
            if position_separator is None:
                block_values = current_block.split(self.delimit)
            else:
                normal_way_count = position_separator
                reverse_way_count = len_block_fields - position_separator - 1
                # total_processed = 0
                block_values = []
                for normal_seq in range(normal_way_count):

                    try:
                        [block_value, current_block] = current_block.split(
                            self.delimit, 1)
                    except ValueError:
                        return row_data
                    block_values.append(block_value)
                for reverse_seq in range(reverse_way_count):
                    try:
                        [current_block, block_value] = current_block.rsplit(
                            self.delimit, 1)
                        block_values.insert(normal_way_count, block_value)
                    except ValueError:
                        return row_data
                block_values.insert(normal_way_count, current_block)
            fragments.extend(block_values)
            if same or regex_field.get("simple_regex") is not None:
                fragments.append(same)

        return fragments


class Report:

    def __init__(self):
        self.data_report = {
            "field_errors": {},
            "row_errors": {},
            "discarded_count": 0,
            "processed_count": 0,
            "real_missing_rows": 0,
            "missing_rows": 0,
            "missing_fields": 0,
            "warnings_fields": 0,
        }

    def add_count(self, field, count=1):
        if field not in self.data_report:
            self.data_report[field] = count
        else:
            self.data_report[field] += count

    def append_missing_row(self, original_data, error=None):
        self.add_count("missing_rows")
        if error:
            self.add_count("real_missing_rows")
            try:
                [error_type, error_detail] = error.split(";", 1)
            except Exception:
                [error_type, error_detail] = [error, "GENERAL"]
            self.add_error("row", error_type, error_detail, original_data)

    def append_missing_field(self, name_column_id, original_value, error):
        if "warning" in error:
            self.add_count("warnings_fields")
        self.add_count("missing_fields")
        self.add_error("field", name_column_id, error, original_value)

    def add_error(self, field, err_type, error, original_data):
        elem = self.data_report[f"{field}_errors"]
        elem.setdefault(err_type, {"count": 0})
        elem[err_type]["count"] += 1
        elem[err_type].setdefault(error, {"count": 0, "examples": []})
        elem[err_type][error]["count"] += 1

        examples = elem[err_type][error]["examples"]
        if len(examples) < 6:
            elem[err_type][error]["examples"].append(original_data)


class Buffers(Report):

    def __init__(
            self, trans_class, model_fields: dict, models_to_save: list,
            final_path: str):
        super().__init__()
        # self.trans_class = trans_class
        self.model_fields = model_fields
        self.models_to_save = models_to_save
        self.buffers = {}
        self.csvs = {}
        self.buffers_by_date = {}
        self.csvs_by_date = {}
        self.all_final_paths = []
        self.all_rx = {}
        self.totals_by_date = {}

        self.final_path = final_path
        self.s3_utils = trans_class.s3_utils
        self.normal_models = [model for model in trans_class.editable_models
                              if model["name"] not in ["drug", "rx"]]
        for model in self.normal_models:
            model_name = model["name"]
            self.csvs[model_name] = io.StringIO()
            self.buffers[model_name] = csv.writer(
                self.csvs[model_name], delimiter="|")
            self.build_headers(model_name)

    def __call__(self, file):
        pass

    def save_missing_rows(self, rows):
        self.buffers["missing_row"].writerows(rows)

    def add_cat_row(self, row_data, cat_name="missing_field"):
        self.buffers[cat_name].writerow(row_data)

    def write_drug_row(self, complex_date, row_data):
        self.buffers_by_date[complex_date].writerow(row_data)
        self.add_count("drugs_count")
        self.totals_by_date[complex_date]["drugs_count"] += 1

    def add_complex_date(self, complex_date):
        if complex_date not in self.all_rx:
            self.all_rx.setdefault(complex_date, {})
            self.totals_by_date.setdefault(
                complex_date, {"drugs_count": 0, "rx_count": 0})
            self.csvs_by_date[complex_date] = io.StringIO()
            self.buffers_by_date[complex_date] = csv.writer(
                self.csvs_by_date[complex_date], delimiter="|")
            headers = []
            for model_name in self.models_to_save:
                model_headers = self.build_headers(model_name, need_return=True)
                headers.extend(model_headers)
            self.buffers_by_date[complex_date].writerow(headers)

    def get_rx_data(self, complex_date, folio_ocamis):
        return self.all_rx.get(complex_date, {}).get(folio_ocamis, {})

    def add_rx(self, complex_date, folio_ocamis, row_data):
        self.all_rx[complex_date][folio_ocamis] = row_data

    def build_headers(self, cat_name, need_return=False):
        if cat_name == "unique_helpers":
            headers = ["medicament_key", "medical_unit_key"]
        else:
            fields = self.model_fields[cat_name]
            headers = [field["name"] for field in fields]
        if need_return:
            return headers
        else:
            self.buffers[cat_name].writerow(headers)

    def count_rx(self):
        for complex_date, folios in self.all_rx.items():
            len_folios = len(folios)
            self.add_count("rx_count", len_folios)
            self.totals_by_date[complex_date]["rx_count"] += len_folios

    def save_csv_cats(self):
        for cat_model in self.normal_models:
            cat_name = cat_model["name"]
            if "missing" in cat_name:
                cat_count = self.data_report.get(f"{cat_name}s", 0)
            else:
                cat_count = self.data_report.get(f"{cat_name}_count", 0)
            if cat_count == 0:
                continue
            only_name = self.final_path.replace("NEW_ELEM_NAME", cat_name)
            self.all_final_paths.append({
                "model": cat_model["model"],
                "path": only_name,
            })
            self.s3_utils.save_csv_in_aws(
                self.csvs[cat_name], only_name, storage_class="STANDARD_IA")

    def save_csvs_by_date(self):
        for complex_date, csv_file in self.csvs_by_date.items():
            iso_year, iso_week, iso_delegation, year, month = complex_date
            date_list = list(complex_date)
            elem_list = list(map(str, date_list))
            elem_name = f"_by_week_{'_'.join(elem_list)}"
            only_name = self.final_path.replace("_NEW_ELEM_NAME", elem_name)
            only_name = only_name.replace("NEW_ELEM_NAME", "by_week")
            self.all_final_paths.append({
                "path": only_name,
                "iso_year": iso_year,
                "iso_week": iso_week,
                "year_week": f"{iso_year}-{iso_week:02d}",
                "iso_delegation_id": iso_delegation,
                "year": year,
                "month": month,
                "year_month": f"{year}-{month:02d}",
                "drugs_count": self.totals_by_date[complex_date]["drugs_count"],
                "rx_count": self.totals_by_date[complex_date]["rx_count"],
            })
            # self.s3_utils.save_csv_in_aws(
            #     csv_file, only_name, storage_class="STANDARD_IA", is_gzip=True)
            self.s3_utils.save_csv_in_aws(
                csv_file, only_name, storage_class="STANDARD_IA", is_gzip=True)


class DateTime:

    def __init__(self, string_date):
        self.string_date = string_date.strip()
        self.string_dates = [
            date_format.strip() for date_format in self.string_date.split(";")]
        self.last_date = None
        self.last_date_formatted = None

    def __call__(self, field, value):
        if value == self.last_date and value:
            return self.last_date_formatted
            # print("same", value)

        format_date = field.get("format_date")
        # print("case")
        if self.string_date == "MANY":
            format_dates = format_date.split(";")
            string_dates = [date.strip() for date in format_dates]
        else:
            string_dates = self.string_dates
        is_success = False
        # print("value initial:", value)
        # print("string_dates:", string_dates)
        for string_format in string_dates:
            try:
                if string_format == "EXCEL":
                    if "." in value:
                        days, seconds = value.split(".")
                        days = int(days)
                        seconds = float("0." + seconds)
                        seconds = round(seconds)
                        # seconds = (float(value) - days) * 86400
                        # value = float(value)
                        # seconds = (value - 25569) * 86400.0
                    else:
                        days = int(value)
                        seconds = 0
                    value = datetime(1899, 12, 30) + timedelta(
                        days=days, seconds=seconds)
                elif string_format == "UNIX":
                    value = datetime.fromtimestamp(int(value))
                else:
                    value = datetime.strptime(value, string_format)
                self.last_date = value
                self.last_date_formatted = value
                is_success = True
                break
            except ValueError:
                pass
            except TypeError:
                pass
            except Exception as e:
                error = f"Error en fecha"
                raise ValueProcessError(error, value, str(e))
        if not is_success:
            error = "No se pudo convertir la fecha"
            raise ValueProcessError(error, value)
        return value

