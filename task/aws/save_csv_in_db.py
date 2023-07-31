import requests
import json
from task.aws.common import request_headers, create_connection, BotoUtils


# def save_csv_in_db(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    lap_sheet_id = event.get("lap_sheet_id")
    entity_month_id = event.get("entity_month_id")
    table_files_ids = event.get("table_files_ids", [])
    db_config = event.get("db_config")
    sql_queries = event.get("sql_queries", [])
    queries_by_model = event.get("queries_by_model", {})
    s3_utils = BotoUtils(event.get("s3"))
    # print("start", datetime.now())
    connection = create_connection(db_config)
    errors = []
    cursor = connection.cursor()
    first_query = event.get("first_query")
    last_query = event.get("last_query")

    def execute_query(query_content, path_file=None, alt_query=None):
        try:
            cursor.execute(query_content)
        except Exception as e:
            errors.append(f"Hubo un error al guardar; {str(e)}")

    # print("before first_query", datetime.now())
    if first_query:
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado la pestaña y su lap")
    # print("after first_query", datetime.now())
    if not errors:
        for sql_query in sql_queries:
            execute_query(sql_query)
    if not errors:
        for model_name, content in queries_by_model.items():
            base_queries = content["base_queries"]
            alternative_query = content.get("alternative_query")
            files = content["files"]
            for query_base in base_queries:
                for path in files:
                    query = query_base.replace("PATH_URL", path)
                    execute_query(query, path, alternative_query)
    if not errors:
        if last_query:
            print("before last_query", datetime.now())
            execute_query(last_query)
        if table_files_ids:
            print("before table_files_ids", datetime.now())
            query = f"UPDATE inai_tablefile SET inserted = true " \
                    f"WHERE id IN ({','.join(table_files_ids)})"
            execute_query(query)
    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    final_result = {
        "lap_sheet_id": lap_sheet_id,
        "entity_month_id": entity_month_id,
        "errors": errors,
        "success": bool(not errors)
    }
    connection.close()
    result_data = {
        "result": final_result,
        "request_id": context.aws_request_id
    }
    json_result = json.dumps(result_data)
    if "webhook_url" in event:
        webhook_url = event["webhook_url"]
        requests.post(webhook_url, data=json_result, headers=request_headers)
    return {
        'statusCode': 200,
        'body': json_result
    }

# data_files/nacional/issste/202107/medicament_3772_default_lap0.csv
# nacional/issste/202107/reporte_recetas_primer_nivel_202105_3.csv
