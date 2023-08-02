import requests
import json
from task.aws.common import request_headers, create_connection, BotoUtils


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")

    first_query = event.get("first_query")
    clean_queries = event.get("clean_queries", [])
    count_query = event.get("count_query")
    drugs_object = event.get("drugs_object")
    # constraint_queries = event.get("constraint_queries", [])
    constraint_queries = []
    insert_queries = event.get("insert_queries", [])
    drop_queries = event.get("drop_queries", [])
    last_query = event.get("last_query")
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

    if not errors and clean_queries:
        for clean_query in clean_queries:
            execute_query(clean_query)

    print("drugs_object", drugs_object)
    # print("before first_query", datetime.now())
    if not errors:
        cursor.execute(count_query)
        week_counts = cursor.fetchall()
        below_weeks = []
        above_weeks = []
        not_founded_weeks = []
        for week_count in week_counts:
            week_id = week_count[0]
            str_week_id = str(week_id)
            count = week_count[1]
            week_count = drugs_object.get(str_week_id)
            if not week_count:
                not_founded_weeks.append(week_id)
            elif week_count == count:
                continue
            elif week_count > count:
                below_weeks.append({week_id: f"{count} vs {week_count}"})
            else:
                above_weeks.append({week_id: f"{count} vs {week_count}"})
        if len(not_founded_weeks) > 0:
            errors.append(f"Hubo {len(not_founded_weeks)} semanas no encontradas \
                en la base de datos, semanas: {not_founded_weeks}")
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
