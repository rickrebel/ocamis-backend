from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from task.models import AsyncTask
from task.helpers import TaskHelper
from datetime import datetime

from inai.misc_mixins.petition_mix import FromAws as Petition
from inai.misc_mixins.week_record_mix import FromAws as WeekRecord
from inai.misc_mixins.month_record_from_aws import FromAws as MonthRecord
from respond.misc_mixins.lap_sheet_mix import FromAws as LapSheet
from respond.misc_mixins.sheet_file_mix import FromAws as SheetFile
from rds.misc_mixins.cluster_mix import FromAws as Cluster
from rds.misc_mixins.mat_view_mix import FromAws as MatView


def extract_only_message(error_text):
    import re
    pattern = r".*[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12} (.*)"
    match = re.search(pattern, error_text)

    if match:
        return match.group(1)
    else:
        return error_text


class AWSErrors(generic.View):

    def get(self, request, *args, **kwargs):
        print("HOLA GET")
        print("request", request)
        return HttpResponse("error")

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        print("HOLA ERRORES")
        print("++++++++++++++++++++++++++++++++++++++++++++++")
        try:
            body = json.loads(request.body)
            print(body)
        except Exception as e:
            print("ERROR AL LEER EL BODY: ", e)
            print("request original: \n", request)
            return HttpResponse()
        try:
            message = body.get("MessageAttributes", {})
            request_id = message.get("RequestID", {}).get("Value")
            if request_id:
                current_task = AsyncTask.objects.get(request_id=request_id)
                # current_task.status_task_id = "not_executed"
                current_task.date_arrive = datetime.now()
                error = message.get("ErrorMessage", {}).get("Value")
                error = extract_only_message(error)
                error = f"AWSError: {error}"
                # current_task.errors = extract_only_message(error)
                current_task.traceback = request.body
                task_helper = TaskHelper(current_task, errors=[error])
                task_helper.comprobate_status()
                # comprobate_status(current_task, error, [])
        except Exception as e:
            print("ERROR AL GUARDAR 1: ", e)
            print("body error 2: \n", body)
        return HttpResponse()


class AWSSuccess(generic.View):

    def get(self, request, *args, **kwargs):
        print("HOLA GET")
        print("request", request)
        return HttpResponse("error")

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        # from task.models import AsyncTask
        # print("HOLA SUCCESS")
        # print(request)
        # print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
        try:
            body = json.loads(request.body)
            # print("body: \n", body)
            # message = body.pop("Message")
            # payload = json.loads(message)
            # print("payload: \n\n", payload, "\n\n")
            # payload_body = payload.pop("body")
            # print("payload_body: \n", payload_body)
        except Exception as e:
            print("ERROR: ", e)
        return HttpResponse()


class AWSMessage(generic.View):

    def get(self, request, *args, **kwargs):
        # print("HOLA GET")
        # print("request", request)
        return HttpResponse("error")

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        # print("HOLA POST")
        # print(request)
        request_body = request.body
        try:
            body = json.loads(request_body)
        except Exception as e:
            print("ERROR AL LEER EL BODY: ", e)
            print("request original: \n", request)
            return HttpResponse()

        try:
            function_aws = AwsFunction(body=body)
            function_aws.execute_function()
            response = "success"
        except Exception as e:
            print("ERROR AL GUARDAR 1: ", e)
            print("body error 1: \n", body)
            response = "error"

        return HttpResponse(response)


class AwsFunction(TaskHelper):

    def __init__(
            self, body=None, main_task=None, parent_task=None):
        # self.body = body
        self.response = None
        self.result = None
        self.errors = []
        self.function_name = None
        self.final_method = None
        if body:
            main_task = self.build_with_body(body)
        super().__init__(main_task, errors=self.errors)
        if parent_task:
            params_after = parent_task.params_after or {}
            self.result = params_after.get("params_finished", {})
            self.function_name = parent_task.finished_function
        else:
            raise Exception("No se ha enviado un resultado o un padre")

    def build_with_body(self, body, request_id=None):
        if not request_id:
            request_id = body.get("request_id")
        # print("body 0: \n", body)
        # print("request_id: ", request_id)
        result = body.get("result", {})
        try:
            main_task = AsyncTask.objects.get(request_id=str(request_id))
            main_task.status_task_id = "success"
            main_task.date_arrive = datetime.now()
            # print("RESULT: ", result)
            main_task.result = result
            main_task.save()
            new_result = result.copy()
            new_result.update(self.main_task.params_after or {})
            self.build_result(new_result)
            # function_aws = AwsFunction(self.main_task, new_result)
            # function_aws.execute_function()
            self.response = "success"
            return main_task
        except Exception as e:
            raise e

    def build_result(self, new_result):
        self.errors = new_result.get("errors", [])
        self.function_name = self.main_task.function_after

    def get_method(self):
        from task.base_views import TaskParams
        task_parameters = {"parent_task": self.main_task}
        try:
            self.final_method = getattr(self.model_obj, self.function_name)
        except AttributeError as error2:
            try:
                model_name = self.model_obj.__class__.__name__
                from_aws_class = globals()[model_name]
                base_task = TaskParams(
                    model_obj=self.model_obj, parent_task=self.main_task)
                base_aws_mix = from_aws_class(
                    self.model_obj, task_param=task_parameters,
                    base_task=base_task)
                self.final_method = getattr(base_aws_mix, self.function_name)
            except Exception as error3:
                err = f"Error al obtener el método {self.function_name}: {error2}"
                err += f"; {error3}"
                self.errors.append(err)
        return self.final_method

    def execute_function(self):
        import traceback

        self.model_obj = self.find_task_model()
        self.result["from_aws"] = True
        self.final_method = self.get_method()
        if self.final_method:
            try:
                self.new_tasks, final_errors, data = self.final_method(
                    **self.result,
                    task_params={"parent_task": self.main_task})
                self.errors.extend(final_errors or [])
            except Exception as error:
                error_ = traceback.format_exc()

                error_ = (f"Error en el método {self.function_name}:"
                          f"{str(error)} {str(error_)}")
                self.errors.append(error_)
        self.main_task.date_end = datetime.now()
        if self.errors:
            print("ERRORES en ExecuteAwsFunction: ", self.errors)
        # return comprobate_status(self.main_task, self.errors, self.new_tasks)
        return self.comprobate_status()
