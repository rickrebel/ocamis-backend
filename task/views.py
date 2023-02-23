from .models import AsyncTask
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


class AWSMessage(generic.View):

    def get(self, request, *args, **kwargs):
        print("HOLA GET")
        print("request", request)
        return HttpResponse("error")

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        from datetime import datetime
        from task.models import AsyncTask
        print("HOLA POST")
        # print(request)
        body = json.loads(request.body)
        # print("body: \n", body)
        request_id = body.get("request_id")
        result = body.get("result", {})
        errors = result.get("errors", [])
        current_task = AsyncTask.objects.get(request_id=request_id)
        current_task.status_task_id = "success"
        current_task.date_arrive = datetime.now()
        current_task.result = result
        current_task.save()
        models = ["petition", "file_control", "process_file", "data_file"]
        function_after = current_task.function_after
        final_errors = []
        new_tasks = []
        for model in models:
            current_obj = getattr(current_task, model)
            if current_obj:
                # print("CURRENT OBJ: ", current_obj)
                # name_model = current_obj.__class__.__name__
                # print("NAME MODEL: ", name_model)
                method = getattr(current_obj, function_after)
                # print("METHOD: ", method)
                task_params = {"parent_task": current_task}
                result["from_aws"] = True
                new_tasks, final_errors, data = method(
                    **result, task_params=task_params)
                break
        errors += (final_errors or [])
        current_task.date_end = datetime.now()
        comprobate_status(current_task, errors, new_tasks)
        return HttpResponse()


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
        print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        from datetime import datetime
        # from task.models import AsyncTask
        print("HOLA ERRORES")
        # print(request)
        print("++++++++++++++++++++++++++++++++++++++++++++++")
        try:
            body = json.loads(request.body)
        except Exception as e:
            print("ERROR AL LEER EL BODY: ", e)
            print("request original: \n", request)
        try:
            message = body.get("MessageAttributes", {})
            request_id = message.get("RequestID", {}).get("Value")
            if request_id:
                current_task = AsyncTask.objects.get(request_id=request_id)
                # current_task.status_task_id = "not_executed"
                current_task.date_arrive = datetime.now()
                error = message.get("ErrorMessage", {}).get("Value")
                error = extract_only_message(error)
                # current_task.errors = extract_only_message(error)
                current_task.traceback = request.body
                comprobate_status(current_task, error, [])
        except Exception as e:
            print("ERROR AL GUARDAR: ", e)
            print("body: \n", body)
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
        from datetime import datetime
        # from task.models import AsyncTask
        print("HOLA SUCCESS")
        # print(request)
        print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
        try:
            body = json.loads(request.body)
            # print("body: \n", body)
            message = body.pop("Message")
            payload = json.loads(message)
            print("payload: \n\n", payload, "\n\n")
            # payload_body = payload.pop("body")
            # print("payload_body: \n", payload_body)
        except Exception as e:
            print("ERROR: ", e)
        return HttpResponse()


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def build_task_params(
        model, function_name, request, subgroup=None):
    from datetime import datetime
    kwargs = {camel_to_snake(model.__class__.__name__): model}

    def update_previous_tasks(tasks):
        # print("TASKS: ", tasks)
        # tasks.update(is_current=False)
        for task in tasks:
            task.is_current = False
            task.save()
            if task.child_tasks.exists():
                update_previous_tasks(task.child_tasks.all())

    update_previous_tasks(AsyncTask.objects.filter(**kwargs))

    if subgroup:
        kwargs["subgroup"] = subgroup
    key_task = AsyncTask.objects.create(
        user=request.user, task_function_id=function_name,
        date_start=datetime.now(), status_task_id="created", **kwargs
    )
    return key_task, {"parent_task": key_task}


def comprobate_status(
        current_task, errors=None, new_tasks=None, want_http_response=False):
    from rest_framework.response import Response
    from rest_framework import status

    if not current_task:
        return None
    if errors:
        current_task.errors = errors
        if isinstance(errors, str):
            status_task_id = "not_executed"
        else:
            status_task_id = "with_errors"
    elif new_tasks:
        status_task_id = "children_tasks"
    else:
        status_task_id = "finished"
    current_task = comprobate_brothers(current_task, status_task_id)
    if want_http_response:
        body_response = {"new_task": current_task.id}
        if errors:
            body_response["errors"] = errors
            return Response(body_response, status=status.HTTP_400_BAD_REQUEST)
        if new_tasks:
            return Response(body_response, status=status.HTTP_200_OK)
        else:
            return None
    return current_task


def comprobate_brothers(current_task, status_task_id):
    try:
        current_task = current_task.save_status(status_task_id)
    except Exception as e:
        print("current_task: ", current_task)
        print("ERROR AL GUARDAR: ", e)
    is_final = current_task.status_task.is_completed
    if is_final and current_task.parent_task:
        brothers_incomplete = AsyncTask.objects.filter(
            parent_task=current_task.parent_task,
            status_task__is_completed=False)
        if brothers_incomplete.exists():
            parent_status_task_id = "children_tasks"
        else:
            parent_status_task_id = "finished"
        comprobate_brothers(current_task.parent_task, parent_status_task_id)
    return current_task
