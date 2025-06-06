import io
from task.aws.common import send_simple_response, BotoUtils


def clean_na(row):
    cols = row.tolist()
    return [col.strip() if isinstance(col, str) else "" for col in cols]


# def xls_to_csv(event, context):
def lambda_handler(event, context):
    import pandas as pd
    import json

    print("start xls_to_csv")
    final_path = event["final_path"]
    only_name = event["only_name"]
    s3_utils = BotoUtils(event.get("s3"))
    # print("final_path", final_path)
    excel_file = pd.ExcelFile(final_path)
    all_sheet_names = excel_file.sheet_names
    many_sheets = len(all_sheet_names) > 10
    n_rows = 40 if many_sheets else 220
    n_end = 15 if many_sheets else 30
    final_sheets = []

    all_sheets = {}
    for sheet_name in all_sheet_names:
        print("sheet_name", sheet_name)
        data_excel = excel_file.parse(
            sheet_name,
            dtype='string', na_filter=False,
            keep_default_na=False, header=None)
        data_excel = data_excel.replace(
            to_replace=[r"\\t|\\n|\\r", "\t|\n|\r", "\|"],
            value=[" > ", " > ", ";"],
            regex=True)
        if data_excel.empty:
            continue
        csv_buffer = io.StringIO()
        total_rows = data_excel.shape[0]
        data_excel.to_csv(
            csv_buffer, index=False, header=False, sep="|", escapechar="\\")
        final_name = f"{only_name}_SHEET_{sheet_name}.csv"
        s3_utils.save_csv_in_aws(csv_buffer, final_name, is_gzip=True)
        head_excel = data_excel.head(n_rows)
        iter_data_head = head_excel.apply(clean_na, axis=1)
        list_val_head = iter_data_head.tolist()
        tail_excel = data_excel.tail(n_end)
        iter_data_tail = tail_excel.apply(clean_na, axis=1)
        list_val_tail = iter_data_tail.tolist()
        sheet_sample_name = f"{only_name}_sample_{sheet_name}.json"
        sheet_sample = {
            "all_data": list_val_head,
            "tail_data": list_val_tail,
        }
        s3_utils.save_json_file(sheet_sample, sheet_sample_name)
        all_sheets[sheet_name] = {
            # "all_data": list_val_head,
            # "tail_data": list_val_tail,
            "sample_path": sheet_sample_name,
            "total_rows": total_rows,
            "final_path": final_name,
        }
        final_sheets.append(final_name)

    result = {
        "new_sheets": all_sheets,
        "all_sheet_names": final_sheets,
    }
    return send_simple_response(event, context, result=result)

