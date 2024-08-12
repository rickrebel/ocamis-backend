from task.aws.common import create_connection, send_simple_response


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    # from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")

    constraint_query = event.get("constraint")

    # print("start", datetime.now())
    connection = create_connection(db_config)
    errors = []
    warnings = []
    cursor = connection.cursor()

    try:
        cursor.execute(constraint_query)
    except Exception as e:
        str_e = str(e)
        if "current transaction is aborted" in str_e:
            return
        errors.append(f"Hubo un error al guardar; \n{constraint_query}; \n{str(e)}")

    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    connection.close()
    errors.extend(warnings)

    return send_simple_response(event, context, errors=errors)
