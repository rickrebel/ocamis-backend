import json
import re
from task.aws.common import obtain_decode


class GetAllData:

    def __init__(self, match_class):
        self.match_class = match_class

        self.s3_utils = match_class.s3_utils
        self.existing_fields = match_class.existing_fields
        self.positioned_fields = [field for field in self.existing_fields
                                  if field["position"] is not None]

        self.fill_columns = "fill_columns" in match_class.global_transformations
        self.is_prepare = match_class.is_prepare
        self.columns_count = match_class.columns_count
        self.string_date = match_class.string_date

        self.delimit = match_class.delimiter or "|"
        self.sep = "\|" if self.delimit == "|" else self.delimit
        self.regex_fields = self.build_regex_and_dates()

    def __call__(self, file):

        file_type = "json" if self.is_prepare else "csv"
        complete_file = self.s3_utils.get_csv_lines(file, file_type)
        if self.is_prepare:
            complete_file = json.loads(complete_file.read())
            data_rows = complete_file.get("all_data", [])
            tail_data = complete_file.get("tail_data", [])
            data_rows.extend(tail_data)
        else:
            data_rows = complete_file.readlines()
            # data_rows = complete_file
        return self.divide_rows(data_rows)

    def divide_rows(self, data_rows):
        import json
        structured_data = []
        sample = data_rows[:50]
        self.match_class.decode = self.match_class.decode or obtain_decode(sample)
        decoded = self.match_class.decode
        if decoded == "latin-1":
            self.match_class.decode_final = 'latin-1'

        if decoded == "unknown":
            raise ValueError("No se pudo decodificar el archivo")

        # for row_seq, row in enumerate(data_rows[begin+1:], start=begin+1):
        for row_seq, row in enumerate(data_rows, start=1):
            self.match_class.last_missing_row = None
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
                structured_data.append(row_final)
            elif self.fill_columns:
                row_final.insert(0, str(row_seq))
                row_final.extend([None] * (self.columns_count - current_count))
                structured_data.append(row_final)
            else:
                error = "Conteo distinto de Columnas; %s de %s" % (
                    current_count, self.columns_count)
                row_data = [str(row_seq), row_data]
                self.match_class.add_missing_row(row_data, error)

        return structured_data

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
        self.data = {
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
        if field not in self.data:
            self.data[field] = count
        else:
            self.data[field] += count

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
        elem = self.data[f"{field}_errors"]
        elem.setdefault(err_type, {"count": 0})
        elem[err_type]["count"] += 1
        elem[err_type].setdefault(error, {"count": 0, "examples": []})
        elem[err_type][error]["count"] += 1

        examples = elem[err_type][error]["examples"]
        if len(examples) < 6:
            elem[err_type][error]["examples"].append(original_data)
