import requests
import json
from task.aws.common import send_simple_response, create_connection


# def validate_temp_tables(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")

    clean_queries = event.get("clean_queries", [])
    count_query = event.get("count_query")
    drugs_object = event.get("drugs_object")
    constraint_queries = event.get("constraint_queries", [])
    # constraint_queries = []
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
        if last_query:
            print("before last_query", datetime.now())
            execute_query(last_query)
    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    connection.close()

    return send_simple_response(errors, event, context)
