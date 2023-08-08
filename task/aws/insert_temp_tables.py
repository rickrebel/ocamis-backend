from task.aws.common import create_connection, send_simple_response


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")
    first_query = event.get("first_query")
    last_query = event.get("last_query")

    clean_queries = event.get("clean_queries", [])
    count_query = event.get("count_query")
    drugs_object = event.get("drugs_object")
    constraint_queries = event.get("constraint_queries", [])

    insert_queries = event.get("insert_queries", [])
    drop_queries = event.get("drop_queries", [])
    # print("start", datetime.now())
    connection = create_connection(db_config)
    errors = []
    cursor = connection.cursor()

    def execute_query(query_content):
        try:
            cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            errors.append(f"Hubo un error al guardar; {str(e)}")

    if first_query:
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado este mes completo")

    if not errors and clean_queries:
        print("before clean_query", datetime.now())
        for clean_query in clean_queries:
            execute_query(clean_query)

    print("drugs_object", drugs_object)
    # print("before first_query", datetime.now())
    if not errors and count_query:
        cursor.execute(count_query)
        week_counts = cursor.fetchall()
        below_weeks = []
        above_weeks = []
        not_founded_weeks = []
        not_inserted_weeks = []
        week_ids_in_db = set()
        for week_count in week_counts:
            week_id = week_count[0]
            str_week_id = str(week_id)
            week_ids_in_db.add(str_week_id)
            count = week_count[1]
            week_count = drugs_object.get(str_week_id)
            if not week_count:
                if count:
                    not_founded_weeks.append(week_id)
            elif week_count == count:
                continue
            elif week_count > count:
                below_weeks.append({week_id: f"{count} vs {week_count}"})
            else:
                above_weeks.append({week_id: f"{count} vs {week_count}"})
        for week_id, week_count in drugs_object.items():
            if week_id not in week_ids_in_db and week_count:
                not_inserted_weeks.append(int(week_id))

        if len(not_founded_weeks) > 0:
            errors.append(f"Hubo {len(not_founded_weeks)} semanas no encontradas \
                en la base de datos, semanas: {not_founded_weeks}; \
                week_counts: {week_counts}")
        if len(not_inserted_weeks) > 0:
            errors.append(f"Hubo {len(not_inserted_weeks)} semanas no insertadas \
                en la base de datos, semanas: {not_inserted_weeks}")
        if len(above_weeks) > 0:
            errors.append(f"Hubo {len(above_weeks)} semanas con más medicamentos \
                de los esperados, semanas: {above_weeks}")
        if len(below_weeks) > 0:
            errors.append(f"Hubo {len(below_weeks)} semanas con menos medicamentos \
                de los esperados, semanas: {below_weeks}")

    if not errors and insert_queries:
        print("before insert_query", datetime.now())
        for insert_query in insert_queries:
            execute_query(insert_query)

    if not errors and constraint_queries:
        print("before constraint_query", datetime.now())
        for constraint in constraint_queries:
            try:
                cursor.execute(constraint)
            except Exception as e:
                str_e = str(e)
                if "already exists" in str_e:
                    continue
                if "multiple primary keys" in str_e:
                    continue
                if "current transaction is aborted" in str_e:
                    continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                errors.append(f"Error en constraint {constraint}; {str(e)}")
                break

    if not errors and drop_queries:
        print("before drop_query", datetime.now())
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

    return send_simple_response(event, context, errors=errors)
