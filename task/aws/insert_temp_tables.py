from task.aws.common import send_simple_response, BotoUtils
from task.aws.query_commons import QueryExecution


# def insert_temp_tables(event, context):
def lambda_handler(event, context):
    import traceback

    query_execution = InsertQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        query_execution.rollback()
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
        self.execute_many_queries(
            create_base_tables, need_raise=False, is_soft=True)

        error_message = "Ya se había insertado este mes completo"
        if first_query := event.get("first_query"):
            self.execute_query(
                first_query, need_raise=False, error_msg=error_message)
        self.comprobate_errors()

        self.execute_many_queries(event.get("clean_queries", []))
        if count_query := event.get("count_query"):
            self._count_query(count_query, event.get("drugs_object"))
        self.constraint_queries(event.get("constraint_queries", []))
        self.execute_many_queries(
            event.get("insert_queries", []), need_sleep=True)
        if export_tables_s3 := event.get("export_tables_s3", []):
            self.execute_many_queries(export_tables_s3, need_sleep=True)
            self.send_to_deep(event)
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

    def send_to_deep(self, event):
        for month_path in event.get("month_paths", []):
            try:
                self.s3_utils.change_storage_class(month_path, "DEEP-ARCHIVE")
            except Exception as e:
                self.errors.append(
                    f"Error al enviar a deep: {month_path}; {str(e)}")
        self.comprobate_errors()
