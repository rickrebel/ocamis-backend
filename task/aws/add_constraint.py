from task.aws.common import create_connection, send_simple_response
from task.aws.query_commons import QueryExecution


# def add_constraint(event, context):
def lambda_handler(event, context):
    # from datetime import datetime
    # print("model_name", event.get("model_name"))

    query_execution = AddQueryExecution(event, context)
    try:
        query_execution.execute_all_queries()
    except Exception as e:
        pass

    return send_simple_response(event, context, errors=query_execution.errors)


class AddQueryExecution(QueryExecution):

    def execute_all_queries(self):
        if constraint_query := self.event.get("constraint"):
            self.constraint_queries([constraint_query])
        if constraint_queries := self.event.get("constraint_queries"):
            self.constraint_queries(constraint_queries)
        self.finish_and_save()
