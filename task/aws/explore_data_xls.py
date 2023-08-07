from task.aws.common import send_simple_response


def clean_na(row):
    cols = row.tolist()
    return [col.strip() if isinstance(col, str) else "" for col in cols]


# def explore_data_xls(event, context):
def lambda_handler(event, context):
    import pandas as pd
    final_path = event["final_path"]
    n_rows = event.get("n_rows", 200)
    n_end = event["n_end"]
    excel_file = pd.ExcelFile(final_path)
    pending_sheets = event.get("sheets", [])
    ready_sheets = event.get("ready_sheets", [])
    all_sheet_names = []
    if not pending_sheets:
        all_sheet_names = excel_file.sheet_names
        pending_sheets = list(set(all_sheet_names) - set(ready_sheets))
    all_sheets = {}
    for sheet_name in pending_sheets:
        data_excel = excel_file.parse(
            sheet_name,
            dtype='string', na_filter=False,
            keep_default_na=False, header=None)
        total_rows = data_excel.shape[0]
        if n_rows:
            data_excel = data_excel.head(n_rows)
        iter_data = data_excel.apply(clean_na, axis=1)
        list_val = iter_data.tolist()
        all_sheets[sheet_name] = {
            "all_data": list_val,
            "total_rows": total_rows,
        }
        if n_end:
            tail_excel = data_excel.tail(n_end)
            iter_data_tail = tail_excel.apply(clean_na, axis=1)
            list_val_tail = iter_data_tail.tolist()
            all_sheets[sheet_name]["tail_data"] = list_val_tail

    result = {
        "new_sheets": all_sheets,
        "all_sheet_names": all_sheet_names
    }
    return send_simple_response(event, context, result=result)
