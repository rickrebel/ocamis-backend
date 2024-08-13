from task.aws.common import send_simple_response, create_connection
from task.aws.query_commons import QueryExecution


def lambda_handler(event, context):
    import traceback
    final_result = {
        "lap_sheet_id": event.get("lap_sheet_id"),
        "month_record_id": event.get("month_record_id")}

    query_execution = SaveQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        if not query_execution.errors:
            print("Exception", e)
            error_ = traceback.format_exc()
            errors = [f"Hay un error raro en la construcción: \n{str(e)}\n{error_}"]
            return send_simple_response(
                event, context, errors=errors, result=final_result)

    return send_simple_response(
        event, context, errors=query_execution.errors, result=final_result)


class SaveQueryExecution(QueryExecution):

    def execute_all_queries(self):
        event = self.event
        first_query = event.get("first_query")
        error_message = "Ya se había insertado la hoja y su lap"
        self.execute_query(first_query, error_msg=error_message)
        self.execute_many_queries(event.get("sql_queries", []))
        # self.execute_many_queries(event.get("queries_by_model", []))
        self._queries_by_model(event.get("queries_by_model", []))
        self.execute_query(event.get("last_query"), need_raise=False)
        self.finish_and_save()

    def _queries_by_model(self, queries_by_model):
        for content in queries_by_model:
            base_queries = content["base_queries"]
            # alternative_query = content.get("alternative_query")
            files = content["files"]
            for query_base in base_queries:
                for path in files:
                    query = query_base.replace("PATH_URL", path)
                    self.execute_query(query, need_raise=False)
        self.comprobate_errors()

    def _update_table_files(self, table_files_ids):
        str_table_files_ids = [str(x) for x in table_files_ids]
        query = f"UPDATE inai_tablefile SET inserted = true " \
                f"WHERE id IN ({','.join(str_table_files_ids)})"
        self.execute_query(query, need_raise=False)
        self.comprobate_errors()


# def save_csv_in_db(event, context):
def lambda_handler_old(event, context):
    from datetime import datetime
    lap_sheet_id = event.get("lap_sheet_id")
    month_record_id = event.get("month_record_id")
    table_files_ids = event.get("table_files_ids", [])
    db_config = event.get("db_config")
    sql_queries = event.get("sql_queries", [])
    queries_by_model = event.get("queries_by_model", [])
    print("start", datetime.now())
    connection = create_connection(db_config)
    print("connection", datetime.now())
    errors = []
    cursor = connection.cursor()
    first_query = event.get("first_query")
    last_query = event.get("last_query")

    def execute_query(query_content, path_file=None, alt_query=None):
        try:
            cursor.execute(query_content)
        except Exception as e:
            errors.append(f"Hubo un error al guardar 6; \n{query_content}; \n{str(e)}")

    # print("before first_query", datetime.now())
    if first_query:
        print("before first_query", datetime.now())
        cursor.execute(first_query)
        result = cursor.fetchone()
        if result[0]:
            errors.append(f"Ya se había insertado la hoja y su lap")
    # print("after first_query", datetime.now())
    if not errors:
        print("before sql_queries", datetime.now())
        for sql_query in sql_queries:
            execute_query(sql_query)
    if not errors:
        print("before queries_by_model", datetime.now())
        # for model_name, content in queries_by_model.items():
        for content in queries_by_model:
            base_queries = content["base_queries"]
            alternative_query = content.get("alternative_query")
            files = content["files"]
            for query_base in base_queries:
                for path in files:
                    query = query_base.replace("PATH_URL", path)
                    execute_query(query, path, alternative_query)
    if not errors:
        if last_query:
            print("before last_query", datetime.now())
            execute_query(last_query)
        if table_files_ids:
            print("before table_files_ids", datetime.now())
            str_table_files_ids = [str(x) for x in table_files_ids]
            query = f"UPDATE inai_tablefile SET inserted = true " \
                    f"WHERE id IN ({','.join(str_table_files_ids)})"
            execute_query(query)
    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    connection.close()

    final_result = {
        "lap_sheet_id": lap_sheet_id,
        "month_record_id": month_record_id,
    }
    return send_simple_response(event, context, errors, final_result)

# data_files/nacional/issste/202107/medicament_3772_default_lap0.csv
# nacional/issste/202107/reporte_recetas_primer_nivel_202105_3.csv
