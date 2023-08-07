from task.aws.common import send_simple_response, BotoUtils


# def forcing_response(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))
    init_data = event["init_data"]
    init_data["s3"] = event["s3"]
    forcing_aws = ForcingAws(init_data, context)
    final_result = forcing_aws.build_response()
    return send_simple_response(event, context, result=final_result)


class ForcingAws:

    def __init__(self, init_data: dict, context):

        self.s3_utils = BotoUtils(init_data.get("s3"))
        self.context = context

    def build_response(self):
        result = {
            "HOLA MUNDO": "HOLA MUNDO"
        }
        return result
