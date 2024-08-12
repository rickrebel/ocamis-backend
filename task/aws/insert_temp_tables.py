from task.aws.common import (
    create_connection, send_simple_response)


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
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


def lambda_handler_new(event, context):
    query_execution = QueryExecution(event, context)
    try:
        query_execution.execute_all_queries(event)
    except Exception as e:
        print("ERRORS:\n", e)
        query_execution.rollback()
    else:
        query_execution.finish_and_save()
    return send_simple_response(event, context, errors=query_execution.errors)


class QueryExecution:

    def __init__(self, event, context):
        self.connection = create_connection(event.get("db_config"))
        self.cursor = self.connection.cursor()
        self.errors = []
        self.warnings = []

    def execute_all_queries(self, event):
        create_base_tables = event.get("create_base_tables")
        first_query = event.get("first_query")
        self.execute_many_queries(create_base_tables, need_raise=False)
        self.execute_query(first_query, need_raise=False)
        if self.errors:
            raise self.errors
        self.execute_many_queries(event.get("clean_queries", []))
        if count_query := event.get("count_query"):
            self._count_query(count_query, event.get("drugs_object"))
        self._constraint_queries(event.get("constraint_queries", []))

    def execute_many_queries(self, queries, need_raise=True):
        for query in queries:
            self.execute_query(query, need_raise)

    def execute_query(self, query_content, need_raise=True):
        try:
            self.cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            self.errors.append(
                f"Hubo un error al guardar; \n{query_content}; \n{str(e)}")
            if need_raise:
                raise self.errors

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

    def _constraint_queries(self, constraint_queries):
        valid_errors = [
            "already exists", "ya existe",
            "multiple primary keys", "tiples llaves primarias",
            "current transaction is aborted",
            "la transacción actual ha sido abortada",
        ]
        for constraint in constraint_queries:
            # print("before constraint_query", datetime.now())
            try:
                self.cursor.execute(constraint)
            except Exception as e:
                str_e = str(e)
                for valid_error in valid_errors:
                    if valid_error in str_e:
                        continue
                # print("constraint", constraint)
                # print(f"ERROR:\n, {e}, \n--------------------------")
                self.errors.append(
                    f"Error en constraint {constraint}; --> {str_e} <--")
                raise self.errors

    def rollback(self):
        self.connection.rollback()
        self.close()

    def finish_and_save(self):
        self.cursor.close()
        self.connection.commit()
        self.close()

    def close(self):
        self.connection.close()
        self.errors.extend(self.warnings)



