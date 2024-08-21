from task.aws.common import create_connection, send_simple_response
from task.aws.query_commons import QueryExecution


# def add_mat_view(event, context):
def lambda_handler(event, context):
    import time
    # from datetime import datetime
    # print("model_name", event.get("model_name"))

    query_execution = AddQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        pass
    time.sleep(6)
    return send_simple_response(event, context, errors=query_execution.errors)


class AddQueryExecution(QueryExecution):

    def execute_all_queries(self):
        main_script = self.event.get("main_script")
        self.constraint_queries([main_script])
        self.finish_and_save()
