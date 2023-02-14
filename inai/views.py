
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


def comprobate_status(current_task, errors=None, new_tasks=None):
    if not current_task:
        return None
    print("ESTOY EN COMPROBATE STATUS")
    is_sync = not current_task.request_id

    if errors:
        print("FINAL ERRORS: ", errors)
        current_task.errors = errors
        status_task_id = "with_errors"
    elif new_tasks:
        status_task_id = "children_tasks"
    elif is_sync:
        current_task.delete()
        return None
    else:
        status_task_id = "finished"
    return comprobate_brothers(current_task, status_task_id)


def comprobate_brothers(current_task, status_task_id):
    from inai.models import AsyncTask
    try:
        current_task = current_task.save_status(status_task_id)
    except Exception as e:
        print("current_task: ", current_task)
        print("ERROR AL GUARDAR: ", e)
    # from category.models import StatusTask
    # is_final = current_task.status_task_id in ["finished", "with_errors"]
    # completed_status = StatusTask.objects.filter(
    #     is_completed=True).values_list("id", flat=True)
    # is_final = current_task.status_task_id in completed_status
    is_final = current_task.status_task.is_completed
    if is_final and current_task.parent_task:
        not_finished = ["pending", "running", "children_tasks"]
        brothers_incomplete = AsyncTask.objects.filter(
            parent_task=current_task.parent_task,
            status_task__is_completed=False)
        if brothers_incomplete.exists():
            parent_status_task_id = "children_tasks"
        else:
            parent_status_task_id = "finished"
        comprobate_brothers(current_task.parent_task, parent_status_task_id)
    return current_task


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
        # print("HOLA POST")
        # print(request)
        body = json.loads(request.body)
        request_id = body.get("request_id")
        result = body.get("result", {})
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
                result["from_aws"] = True
                new_tasks, final_errors, data = method(
                    **result, task_params=task_params)
                break
        errors += final_errors
        comprobate_status(current_task, errors=errors, new_tasks=new_tasks)
        return HttpResponse()

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
        from inai.models import AsyncTask
        print("HOLA POST")
        # print(request)
        #body = json.loads(request.body)
        #print("body: \n", body)
        return HttpResponse()
