import requests
import json
from task.aws.common import request_headers, create_connection, BotoUtils


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    raise Exception("No se puede ejecutar esta función")
    # print("model_name", event.get("model_name"))
    lap_sheet_id = event.get("lap_sheet_id")
    entity_month_id = event.get("entity_month_id")
    db_config = event.get("db_config")

    first_query = event.get("first_query")
    count_query = event.get("count_query")
    drugs_counts = event.get("drugs_counts")
    constraint_queries = event.get("constraint_queries", [])
    insert_queries = event.get("insert_queries", [])
    drop_queries = event.get("drop_queries", [])
    last_query = event.get("last_query")

    queries_by_model = event.get("queries_by_model", {})
    # print("start", datetime.now())
    connection = create_connection(db_config)
    errors = []
    cursor = connection.cursor()

    def execute_query(query_content, path_file=None, alt_query=None):
        try:
            cursor.execute(query_content)
        except Exception as e:
            errors.append(f"Hubo un error al guardar; {str(e)}")

    if first_query:
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado este mes completo")

    # print("before first_query", datetime.now())
    if not errors:
        cursor.execute(count_query)
        week_counts = cursor.fetchall()
        below_weeks = []
        above_weeks = []
        for week_count in week_counts:
            week_id = week_count[0]
            count = week_count[1]
            week_count = drugs_counts.get(id=week_id)
            if week_count == count:
                continue
            elif week_count > count:
                below_weeks.append(week_id)
            else:
                above_weeks.append(week_id)
        if len(above_weeks) > 0:
            errors.append(f"Hubo {len(above_weeks)} semanas con más medicamentos \
                de los esperados, semanas: {above_weeks}")
        if len(below_weeks) > 0:
            errors.append(f"Hubo {len(below_weeks)} semanas con menos medicamentos \
                de los esperados, semanas: {below_weeks}")

    if not errors:
        for constraint in constraint_queries:
            try:
                cursor.execute(constraint)
            except Exception as e:
                str_e = str(e)
                if "already exists" in str_e:
                    continue
                if "multiple primary keys" in str_e:
                    continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                errors.append(f"Error en constraint {constraint}; {str(e)}")
                break

    if not errors:
        for insert_query in insert_queries:
            execute_query(insert_query)

    # if not errors:
    #     for drop_query in drop_queries:
    #         execute_query(drop_query)

    if not errors:
        if last_query:
            print("before last_query", datetime.now())
            execute_query(last_query)
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
