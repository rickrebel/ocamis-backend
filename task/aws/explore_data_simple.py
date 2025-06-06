from task.aws.common import (
    calculate_delimiter, obtain_decode, decode_content,
    send_simple_response, BotoUtils)


def divide_rows(rows, delimiter):
    # print("DIVIDE_ROWS", rows)
    final_rows = []
    for row_seq, row in enumerate(rows, 1):
        # print("\n")
        row_data = row.split(delimiter)
        final_rows.append(row_data)
    return final_rows


def calculate_delimiter_own(data):
    if "|" not in data[:3000]:
        return ","
    else:
        return "|"


# def explore_data_simple(event, context):
def lambda_handler(event, context):
    import json

    errors = []

    file = event["file"]
    s3 = event.get("s3")
    s3_utils = BotoUtils(s3)

    complete_file = s3_utils.get_object_bytes(file)
    data_rows = complete_file.readlines()
    # print("INICIO", data_rows)
    total_rows = len(data_rows)
    data_rows = data_rows[:220]
    tail_data = data_rows[-50:]
    # print("FINAL", data_rows)
    decode = event.get("decode")
    delimiter = event.get("delimiter")
    sample_path = event.get("sample_path")

    result = {}
    if not decode:
        decode = obtain_decode(data_rows)
        # print("DECODE", decode)
        if decode == "unknown":
            errors.append("No se pudo decodificar el archivo")

    if not errors:

        first_rows = decode_content(data_rows, decode)
        if not delimiter:
            delimiter = calculate_delimiter(first_rows)
        validated_data_default = divide_rows(first_rows, delimiter)
        tail_rows = decode_content(tail_data, decode)
        validated_tail = divide_rows(tail_rows, delimiter)
        sample_data = {
            "all_data": validated_data_default[:200],
            "tail_data": validated_tail,
        }
        s3_utils.save_json_file(sample_data, sample_path)

        validated_data = {
            "default": {
                # "all_data": validated_data_default[:200],
                "total_rows": total_rows,
                # "final_path": sample_path,
                "sample_path": sample_path,
            }
        }
        result["new_sheets"] = validated_data
        result["all_sheet_names"] = ["default"]
        result["decode"] = decode
    return send_simple_response(event, context, errors=errors, result=result)
