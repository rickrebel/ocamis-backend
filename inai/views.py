
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


def comprobate_brothers(current_task):
    from inai.models import AsyncTask
    is_final = current_task.status_task_id in ["finished", "with_errors"]
    try:
        current_task.save()
    except Exception as e:
        print("current_task: ", current_task)
        print("ERROR AL GUARDAR: ", e)
    if is_final and current_task.parent_task:
        not_finished = ["pending", "running", "children_tasks"]
        brother_tasks = AsyncTask.objects.filter(
            parent_task=current_task.parent_task,
            status_task_id__in=not_finished)
        if brother_tasks.exists():
            current_task.parent_task.status_task_id = "children_tasks"
        else:
            current_task.parent_task.status_task_id = "finished"
        comprobate_brothers(current_task.parent_task)


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
        from inai.models import AsyncTask
        print("HOLA POST")
        print(request)
        body = json.loads(request.body)
        request_id = body.get("request_id")
        result = body.get("result")
        errors = result.get("errors", [])
        current_task = AsyncTask.objects.get(request_id=request_id)
        current_task.status_task_id = "success"
        current_task.date_end = datetime.now()
        current_task.result = result
        current_task.save()
        models = ["petition", "file_control", "process_file", "data_file"]
        function_after = current_task.function_after
        final_errors = []
        new_tasks = []
        for model in models:
            current_obj = getattr(current_task, model)
            if current_obj:
                print("CURRENT OBJ: ", current_obj)
                name_model = current_obj.__class__.__name__
                print("NAME MODEL: ", name_model)
                method = getattr(current_obj, function_after)
                task_params = {"parent_task": current_task}
                new_tasks, final_errors = method(
                    **result, task_params=task_params)
                break

        if final_errors:
            print("FINAL ERRORS: ", final_errors)
            errors += final_errors
            current_task.errors = errors
            current_task.status_task_id = "with_errors"

        elif new_tasks:
            current_task.status_task_id = "children_tasks"
        else:
            current_task.status_task_id = "finished"
        comprobate_brothers(current_task)
        return HttpResponse()
