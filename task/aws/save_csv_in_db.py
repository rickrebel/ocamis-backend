from task.aws.common import send_simple_response, create_connection
from task.aws.query_commons import QueryExecution


# def save_csv_in_db(event, context):
def lambda_handler(event, context):
    import traceback
    final_result = {
        "lap_sheet_id": event.get("lap_sheet_id"),
        "month_record_id": event.get("month_record_id")}

    query_execution = SaveQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        query_execution.rollback()
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
                    # query = query.replace(", price,", ",")
                    self.execute_query(query, need_raise=False)
        self.comprobate_errors()

    def _update_table_files(self, table_files_ids):
        str_table_files_ids = [str(x) for x in table_files_ids]
        query = f"UPDATE inai_tablefile SET inserted = true " \
                f"WHERE id IN ({','.join(str_table_files_ids)})"
        self.execute_query(query, need_raise=False)
        self.comprobate_errors()
