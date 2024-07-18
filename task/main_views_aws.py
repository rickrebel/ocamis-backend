from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import traceback

from task.models import AsyncTask
from task.helpers import TaskHelper, HttpResponseError


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
            AwsBody(body=body)
            response = "success"
        except Exception as e:
            error_ = traceback.format_exc()
            print("ERROR AL GUARDAR 1: ", e)
            print("LOG:\n", error_)
            print("body error 1: \n", body)
            response = "error"

        return HttpResponse(response)


class AwsFunction(TaskHelper):

    def __init__(
            self, main_task: AsyncTask, parent_task=None,
            function_name=None, new_result=None, **kwargs):

        self.response = None
        self.new_result = new_result or {}
        self.errors = self.new_result.get("errors", [])

        if error_message := kwargs.get("errorMessage"):
            self.errors.append(error_message)
        self.from_aws = True
        self.next_function = function_name
        self.final_method = None

        super().__init__(main_task, errors=self.errors, **kwargs)
        # if function_name:
        #     self.next_function = function_name
        #     print("-x function_name 1.1: ", self.next_function)
        if parent_task:
            # params_after = parent_task.params_after or {}
            # self.new_result = params_after.get("params_finished", {})
            self.next_function = parent_task.finished_function
        elif not self.next_function:
            self.next_function = main_task.task_function.name

    def execute_next_function(self, function_name=None):
        if function_name:
            self.next_function = function_name
        self.model_obj = self._find_task_model()
        self.new_result["from_aws"] = True
        self.final_method = self._get_method()
        if self.final_method:
            try:
                self.final_method(**self.new_result)
                # else:
                #     new_tasks, final_errors, _data = self.final_method(
                #         **self.new_result)
                #     self.errors.extend(final_errors or [])
            except HttpResponseError as e:
                self.add_errors(e.errors, comprobate=False)
            except Exception as error:
                error_tb = traceback.format_exc()
                print("LOG DE ERRORES 2: ", error_tb)
                error_tb = (f"Error en el método {self.next_function}:"
                            f"{str(error)} | {str(error_tb)}")
                self.errors.append(error_tb)

        self.main_task.date_end = datetime.now()
        if self.errors:
            print("ERRORES en ExecuteAwsFunction: ", self.errors)
        # return comprobate_status(self.main_task, self.errors, self.new_tasks)
        return self.comprobate_status(want_http_response=False)

    def _get_method(self):
        from inai.misc_mixins.week_record_mix import FromAws as WeekRecord
        from inai.misc_mixins.month_record_from_aws import FromAws as MonthRecord
        from respond.misc_mixins.lap_sheet_mix import FromAws as LapSheet
        from respond.misc_mixins.sheet_file_mix import FromAws as SheetFile
        from rds.misc_mixins.cluster_mix import FromAws as Cluster
        from rds.misc_mixins.mat_view_mix import FromAws as MatView
        from respond.reply_file_mixins.reply_mix import FromAws as ReplyFile
        task_parameters = {"parent_task": self.main_task}
        try:
            self.final_method = getattr(self.model_obj, self.next_function)
            return self.final_method
        except AttributeError as error2:
            try:
                model_name = self.model_obj.__class__.__name__
                from_aws_class = locals()[model_name]
                # base_task = TaskBuilder(
                #     model_obj=self.model_obj, parent_task=self.main_task)
                # base_task = TaskBuilder(main_task=self.main_task, from_aws=True)
                base_aws_mix = from_aws_class(self.model_obj, base_task=self)
                return getattr(base_aws_mix, self.next_function)
            except Exception as error3:
                error_ = traceback.format_exc()
                print("LOG DE ERRORES 3: ", error_)
                err = f"Error al obtener el método {self.next_function}: {error2}"
                err += f"; {error3}"
                self.errors.append(err)
                return None


class AwsBody(AwsFunction):

    def __init__(self, body: dict, **kwargs):
        request_id = body.get("request_id")
        # print("-x BODY: ", body)
        result = body.get("result", {})
        main_task = AsyncTask.objects.get(request_id=str(request_id))
        main_task.status_task_id = "success"
        main_task.date_arrive = datetime.now()
        # print("RESULT: ", result)
        main_task.result = result
        main_task.save()
        new_result = result.copy()
        super().__init__(main_task=main_task, new_result=new_result)
        self.execute_next_function()
