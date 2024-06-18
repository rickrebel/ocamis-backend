from fixture.pruebas.request_join import initial
from task.aws.common import (
    calculate_delivered_final, send_simple_response, BotoUtils,
    convert_to_str, text_normalizer)
from task.aws.complement import GetAllData
import re


class MatchClass(GetAllData):

    def __init__(self):
        self.init_data = initial.get('init_data')
        self.existing_fields = self.init_data.get('existing_fields')
        self.positioned_fields = [field for field in self.existing_fields
                                  if field["position"] is not None]
        self.s3_utils = BotoUtils(initial.get('s3'))
        self.is_prepare = False
        self.global_transformations = []
        self.columns_count = 14
        self.delimit = ','
        self.delimiter = ','
        self.sep = ","
        self.string_date = "MANY"
        super().__init__(self)

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
                    results.extend(["", ""])
            elif len(results) == 2:
                results.append("")
            return results, re_field["position"]

        prev_pos = None
        next_pos = 1
        remain_block = row_data
        print(f"\n\nrow_data\n", row_data)
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
            print(f"\n\n{regex_field.get('name', '?????')}")
            print(f"\n{regex_field}")
            print(f"\nres\n", res)
            print(f"\nblock_fields\n", block_fields)
            print(f"\nremain_block for\n", remain_block)
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
                        print("More than one separator")
                        return row_data
            # fields_with_separator = [field for field in block_fields
            #                          if field.get("clean_function") == "same_separator"]
            # some_has_separator = any(fields_with_separator)
            # len_with_separator = len(fields_with_separator)
            print("position_separator", position_separator)
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
                        print("Error", current_block)
                        return row_data
                    block_values.append(block_value)
                for reverse_seq in range(reverse_way_count):
                    try:
                        [current_block, block_value] = current_block.rsplit(
                            self.delimit, 1)
                        block_values.insert(normal_way_count, block_value)
                    except ValueError:
                        print("Error ValueError", current_block)
                        return row_data
                block_values.insert(normal_way_count, current_block)
            fragments.extend(block_values)
            if same or regex_field.get("simple_regex") is not None:
                fragments.append(same)

        return fragments
