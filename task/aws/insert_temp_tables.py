from task.aws.common import (
    create_connection, send_simple_response)
from task.aws.query_commons import QueryExecution


def lambda_handler(event, context):
    import traceback

    query_execution = InsertQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        if not query_execution.errors:
            print("Exception", e)
            error_ = traceback.format_exc()
            errors = [f"Hay un error raro en la construcción: \n{str(e)}\n{error_}"]
            return send_simple_response(event, context, errors=errors)

    return send_simple_response(event, context, errors=query_execution.errors)


class InsertQueryExecution(QueryExecution):

    def execute_all_queries(self):
        event = self.event
        create_base_tables = event.get("create_base_tables", [])
        self.execute_many_queries(create_base_tables, need_raise=False)

        error_message = "Ya se había insertado este mes completo"
        first_query = event.get("first_query")
        self.execute_query(first_query, need_raise=False, error_msg=error_message)
        self.comprobate_errors()

        self.execute_many_queries(event.get("clean_queries", []))
        if count_query := event.get("count_query"):
            self._count_query(count_query, event.get("drugs_object"))
        self.constraint_queries(event.get("constraint_queries", []))
        self.execute_many_queries(event.get("insert_queries", []))
        self.execute_many_queries(event.get("drop_queries", []))
        if last_query := event.get("last_query"):
            self.execute_query(last_query)
        self.finish_and_save()

    def _count_query(self, query_content, drugs_object):
        self.cursor.execute(query_content)
        week_counts = self.cursor.fetchall()
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

        comparisons = [
            (not_founded_weeks, "no encontradas", True),
            (not_inserted_weeks, "no insertadas", False),
            (above_weeks, "con más medicamentos", False),
            (below_weeks, "con menos medicamentos", False),
        ]
        for weeks, message, add_week_counts in comparisons:
            message = f"Hubo {len(weeks)} semanas {message} en la base de datos"
            if len(weeks) > 0:
                message += f", semanas: {weeks}"
                if add_week_counts:
                    message += f"; week_counts: {week_counts}"
                self.warnings.append(message)


# def insert_temp_tables(event, context):
def lambda_handler_old(event, context):
    from datetime import datetime
    # print("model_name", event.get("model_name"))
    db_config = event.get("db_config")

    create_base_tables = event.get("create_base_tables")
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
    warnings = []
    cursor = connection.cursor()

    def execute_query(query_content):
        try:
            cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            errors.append(f"Hubo un error al guardar; \n{query_content}; \n{str(e)}")

    if create_base_tables:
        for create_base_table in create_base_tables:
            execute_query(create_base_table)

    if first_query:
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado este mes completo")

    if not errors and clean_queries:
        # print("before clean_query", datetime.now())
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

        comparisons = [
            (not_founded_weeks, "no encontradas", True),
            (not_inserted_weeks, "no insertadas", False),
            (above_weeks, "con más medicamentos", False),
            (below_weeks, "con menos medicamentos", False),
        ]
        for weeks, message, add_week_counts in comparisons:
            message = f"Hubo {len(weeks)} semanas {message} en la base de datos"
            if len(weeks) > 0:
                message += f", semanas: {weeks}"
                if add_week_counts:
                    message += f"; week_counts: {week_counts}"
                warnings.append(message)

    valid_errors = [
        "already exists", "ya existe",
        "multiple primary keys", "tiples llaves primarias",
        "current transaction is aborted",
        "la transacción actual ha sido abortada",
    ]
    if not errors and constraint_queries:
        # print("before constraint_query", datetime.now())
        for constraint in constraint_queries:
            try:
                cursor.execute(constraint)
            except Exception as e:
                str_e = str(e)
                for valid_error in valid_errors:
                    if valid_error in str_e:
                        continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                errors.append(f"Error en constraint {constraint}; --> {str_e} <--")
                break

    if not errors and insert_queries:
        # print("before insert_query", datetime.now())
        for insert_query in insert_queries:
            execute_query(insert_query)

    if not errors and drop_queries:
        # print("before drop_query", datetime.now())
        for drop_query in drop_queries:
            execute_query(drop_query)

    if not errors:
        if last_query:
            # print("before last_query", datetime.now())
            execute_query(last_query)

    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()

    connection.close()
    errors.extend(warnings)

    return send_simple_response(event, context, errors=errors)
