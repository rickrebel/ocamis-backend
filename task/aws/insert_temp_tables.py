import requests
import json
from task.aws.common import create_connection, send_simple_response


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")

    first_query = event.get("first_query")
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

    # print("before first_query", datetime.now())

    if not errors:
        for insert_query in insert_queries:
            execute_query(insert_query)

    if not errors:
        for drop_query in drop_queries:
            execute_query(drop_query)

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
