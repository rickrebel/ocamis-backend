from task.aws.common import send_simple_response, BotoUtils
from task.aws.query_commons import QueryExecution


# def save_cat_tables(event, context):
def lambda_handler(event, context):
    import traceback
    final_result = {
        "table_files_ids": event.get("table_files_ids"),
        "month_record_id": event.get("month_record_id")}

    query_execution = SaveCats(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        query_execution.rollback()
        if not query_execution.errors:
            print("Exception", e)
            error_ = traceback.format_exc()
            errors = [f"Hay un error poco común: \n{str(e)}\n{error_}"]
            return send_simple_response(
                event, context, errors=errors, result=final_result)

    return send_simple_response(
        event, context, errors=query_execution.errors, result=final_result)


class SaveCats(QueryExecution):

    def __init__(self, event, context):
        super().__init__(event, context)
        self.s3_utils = BotoUtils(event.get("s3"))
        self.model_in_db = event.get("model_in_db")
        self.headers = []
        self.saved_hashes = set()
        self.all_hashes = {}
        self.columns_join = ""

    def execute_all_queries(self):
        event = self.event
        table_files_paths = event.get("table_files_paths")
        self._join_all_files(table_files_paths)
        len_hashes = len(self.all_hashes)
        if len_hashes > 200:
            self._keep_only_new_hashes()
        else:
            self._simple_insert()

        if table_files_ids := event.get("table_files_ids"):
            self._update_table_files(table_files_ids)
        self.finish_and_save()

    def _reconfig_headers(self, headers):
        # replace if exist the "provider_id" column with "entity_id"
        if "entity_id" in headers:
            headers[headers.index("entity_id")] = "provider_id"
        return headers

    def _join_all_files(self, table_files_paths):
        for csv_path in table_files_paths:
            csv_content = self.s3_utils.get_object_file(csv_path)
            for (idx, row) in enumerate(csv_content):
                if idx == 0:
                    headers = self._reconfig_headers(row)
                    if not self.headers:
                        self.headers = headers
                    elif self.headers != headers:
                        error = (f"Las cabeceras no coinciden: "
                                 f"{self.headers} != {headers}")
                        self.add_error_and_raise(error)
                else:
                    hex_hash = row[0]
                    if not self.all_hashes.get(hex_hash):
                        self.all_hashes[hex_hash] = tuple(row)
        self.columns_join = ",".join(self.headers)

    def _keep_only_new_hashes(self):
        query = f"SELECT hex_hash FROM {self.model_in_db}"
        self.cursor.execute(query)
        self.saved_hashes = {x[0] for x in self.cursor.fetchall()}
        new_hashes = set(self.all_hashes.keys()) - self.saved_hashes
        new_values = [tuple(v) for k, v in self.all_hashes.items()
                      if k in new_hashes]
        self._mogrify_and_insert(new_values, self.model_in_db)

    def _simple_insert(self):
        temp_table = f"temp_{self.model_in_db}"
        init_query = f"""
            CREATE TEMP TABLE {temp_table} AS SELECT * 
            FROM {self.model_in_db} WITH NO DATA;
        """
        self.execute_query(init_query)
        all_values = [tuple(v) for v in self.all_hashes.values()]
        self._mogrify_and_insert(all_values, temp_table)

        main_query = f"""
            INSERT INTO {self.model_in_db} ({self.columns_join})
                SELECT {self.columns_join}
                FROM {temp_table}
                WHERE NOT EXISTS (
                    SELECT 1 FROM {self.model_in_db} 
                    WHERE {self.model_in_db}.hex_hash = {temp_table}.hex_hash
                );
        """
        self.execute_query(main_query)
        self.execute_query(f"DROP TABLE {temp_table}")

    def _mogrify_and_insert(self, values, final_model=None):
        if not values:
            return
        processed_values = [
            tuple(None if item == '' else item for item in row)
            for row in values]
        s_data = ["%s" for _ in range(len(self.headers))]
        s_content = ",".join(s_data)
        args = ','.join(self.cursor.mogrify(f"({s_content})", x).decode("utf-8")
                        for x in processed_values)
        query = f"INSERT INTO {final_model} ({self.columns_join}) VALUES {args}"
        self.execute_query(query)
