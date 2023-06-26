import requests
import json
from task.aws.common import request_headers, create_connection


# def save_csv_in_db(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))
    lap_sheet_id = event.get("lap_sheet_id")
    entity_month_id = event.get("entity_month_id")
    db_config = event.get("db_config")
    sql_queries = event.get("sql_queries", [])
    queries_by_model = event.get("queries_by_model", {})
    connection = create_connection(db_config)
    errors = []
    cursor = connection.cursor()
    first_query = event.get("first_query")
    last_query = event.get("last_query")
    if first_query:
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado la pestaña y su lap")
    if not errors:
        try:
            for sql_query in sql_queries:
                cursor.execute(sql_query)
            for model_name, content in queries_by_model.items():
                base_queries = content["base_queries"]
                files = content["files"]
                for query_base in base_queries:
                    for path in files:
                        query = query_base.replace("PATH_URL", path)
                        cursor.execute(query)
            cursor.close()
            connection.commit()
        except Exception as e:
            connection.rollback()
            errors.append(f"Hubo un error al guardar; {str(e)}")
    if last_query:
        cursor.execute(last_query)
        result = cursor.fetchone()
        if not result[0]:
            errors.append(f"Hubo un error al ejecutar la última consulta")
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
