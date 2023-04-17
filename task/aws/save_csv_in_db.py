import requests
import json
request_headers = {"Content-Type": "application/json"}


# def save_csv_in_db(event, context):
def lambda_handler(event, context):
    import psycopg2
    print("model_name", event.get("model_name"))
    table_file_id = event.get("table_file_id")
    db_config = event.get("db_config")
    sql_queries = event.get("sql_queries")
    connection = psycopg2.connect(
        database=db_config.get("NAME"),
        user=db_config.get("USER"),
        password=db_config.get("PASSWORD"),
        host=db_config.get("HOST"),
        port=db_config.get("PORT"))

    final_result = {
        "table_file_id": table_file_id,
    }
    try:
        cursor = connection.cursor()
        for sql_query in sql_queries:
            cursor.execute(sql_query)
        connection.commit()
        cursor.close()
        connection.close()
        final_result["success"] = True
    except Exception as e:
        print("model_name", event.get("model_name"))
        # print("sql_query", sql_queries)
        # print("error", e)
        final_result["errors"] = [f"Hubo un error al guardar {str(e)}"]
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
