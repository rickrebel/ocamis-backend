from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import traceback

from task.models import AsyncTask
from task.helpers import TaskHelper


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
            print("ERROR AL GUARDAR 1.2: ", e)
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
            error_ = traceback.format_exc()
            print("ERROR AL GUARDAR 1: ", e)
            print("LOG:\n", error_)
            print("body error 1: \n", body)
            response = "error"

        return HttpResponse(response)


class AwsFunction(TaskHelper):

    def __init__(self, body=None, main_task=None, parent_task=None,
                 function_name=None):
        # self.body = body
        self.response = None
        self.new_result = {}
        self.errors = []
        self.from_aws = True
        self.function_name = None
        self.final_method = None
        if not body and not main_task:
            raise Exception("No se ha enviado un resultado o un main_task")
        if body:
            # print("-x BODY: ", body)
            main_task = self._build_with_body(body)
        super().__init__(main_task, errors=self.errors)
        # if function_name:
        #     self.function_name = function_name
        #     print("-x function_name 1.1: ", self.function_name)
        if parent_task:
            params_after = parent_task.params_after or {}
            self.new_result = params_after.get("params_finished", {})
            self.function_name = parent_task.finished_function
        elif not self.function_name:
            self.function_name = main_task.task_function.name

    def _build_with_body(self, body, request_id=None):
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
            self.new_result = result.copy()
            self.new_result.update(main_task.params_after or {})
            self._build_complement(main_task)
            # function_aws = AwsFunction(self.main_task, new_result)
            # function_aws.execute_function()
            self.response = "success"
            return main_task
        except Exception as e:
            raise e

    def _build_complement(self, main_task=None):
        if not main_task:
            main_task = self.main_task
        self.errors = self.new_result.get("errors", [])
        self.function_name = main_task.function_after

    def _get_method(self):
        from inai.misc_mixins.petition_mix import FromAws as Petition
        from inai.misc_mixins.week_record_mix import FromAws as WeekRecord
        from inai.misc_mixins.month_record_from_aws import FromAws as MonthRecord
        from respond.misc_mixins.lap_sheet_mix import FromAws as LapSheet
        from respond.misc_mixins.sheet_file_mix import FromAws as SheetFile
        from rds.misc_mixins.cluster_mix import FromAws as Cluster
        from rds.misc_mixins.mat_view_mix import FromAws as MatView
        from respond.reply_file_mixins.process_real_mix import FromAws as ReplyFile
        task_parameters = {"parent_task": self.main_task}
        try:
            self.final_method = getattr(self.model_obj, self.function_name)
        except AttributeError as error2:
            try:
                model_name = self.model_obj.__class__.__name__
                from_aws_class = locals()[model_name]
                # base_task = TaskBuilder(
                #     model_obj=self.model_obj, parent_task=self.main_task)
                # base_task = TaskBuilder(main_task=self.main_task, from_aws=True)
                base_aws_mix = from_aws_class(
                    self.model_obj, task_params=task_parameters,
                    base_task=self)
                self.final_method = getattr(base_aws_mix, self.function_name)
            except Exception as error3:
                error_ = traceback.format_exc()
                print("LOG DE ERRORES 3: ", error_)
                err = f"Error al obtener el método {self.function_name}: {error2}"
                err += f"; {error3}"
                self.errors.append(err)
        return self.final_method

    def execute_function(self):

        self.model_obj = self._find_task_model()
        self.new_result["from_aws"] = True
        self.final_method = self._get_method()
        if self.final_method:
            try:
                self.new_tasks, final_errors, data = self.final_method(
                    **self.new_result,
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
        return self.comprobate_status(want_http_response=False)
