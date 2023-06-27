from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import datetime

from classify_task.models import TaskFunction
from task.models import AsyncTask

from inai.misc_mixins.entity_week_mix import FromAws as EntityWeek
from inai.misc_mixins.entity_month_mix import FromAws as EntityMonth
from inai.misc_mixins.lap_sheet_mix import FromAws as LapSheet
from inai.misc_mixins.petition_mix import FromAws as Petition
from inai.misc_mixins.sheet_file_mix import FromAws as SheetFile


def text_normalizer(text):
    import re
    import unidecode
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)


def calculate_special_function(special_function):
    import json
    from geo.models import Delegation, CLUES

    # print("SPECIAL FUNCTION", special_function)
    delegation_value_list = [
        'name', 'other_names', 'id', 'clues_id']

    delegation_name = special_function.get("delegation_name")
    clues_id = special_function.get("clues_id")
    institution_id = special_function.get("institution_id")
    valid_strings = ["H.R.", "HAE ", "C.M.N."]
    final_delegation = None
    standard_name = text_normalizer(delegation_name)
    try:
        curr_delegation = Delegation.objects.get(
            name__icontains=standard_name)
        final_delegation = {}
        for field in delegation_value_list:
            final_delegation[field] = getattr(curr_delegation, field)
        error = None
    except Delegation.DoesNotExist:
        error = f"No se encontró la delegación; {delegation_name}"
    except Delegation.MultipleObjectsReturned:
        error = f"Hay más de una delegación con el mismo nombre; {delegation_name}"

    is_valid_name = any(
        [valid_string in delegation_name for valid_string in valid_strings])

    if not final_delegation and is_valid_name:
        try:
            clues_obj = CLUES.objects.get(id=clues_id)
            del_obj, created = Delegation.objects.get_or_create(
                institution_id=institution_id,
                name=delegation_name,
                clues=clues_obj,
                state=clues_obj.state,
            )
            final_delegation = {}
            for field in delegation_value_list:
                final_delegation[field] = getattr(del_obj, field)
            # self.catalog_delegation[delegation_name] = final_delegation
            # return delegation_id, None
        except Exception as e:
            error = "No se pudo crear la delegación; ERROR: %s" % e
    if not final_delegation and not error:
        error = f"No es un nombre válido, razón desconocida; {delegation_name}"
    response = json.dumps([final_delegation, error])
    return HttpResponse(response)


def find_task_model(async_task):
    task_models = [
        "petition", "file_control", "reply_file", "sheet_file",
        "data_file", "entity_week", "entity_month"]
    for model in task_models:
        current_obj = getattr(async_task, model)
        if current_obj:
            return model, current_obj


def execute_function_aws(current_task, function_name, result, errors=None):

    if not errors:
        errors = []

    final_errors = []
    new_tasks = []

    def get_method(model_obj):
        task_parameters = {"parent_task": current_task}
        final_method = None
        err = ""
        try:
            final_method = getattr(model_obj, function_name)
        except Exception as error2:
            err = f"Error al obtener el método {function_name}: {error2}"
        if not final_method:
            try:
                model_name = model_obj.__class__.__name__
                from_aws_class = globals()[model_name]
                aws_mix = from_aws_class(model_obj, task_parameters)
                final_method = getattr(aws_mix, function_name)
                # return method(**kwargs)
                # final_method = getattr(model_obj, "from_aws")
                # task_parameters["function_name"] = function_name
            except Exception as error3:
                err += f"; {error3}"
                pass
        return final_method, task_parameters, err

    model, current_obj = find_task_model(current_task)
    # print("CURRENT OBJ: ", current_obj)
    # name_model = current_obj.__class__.__name__
    # print("NAME MODEL: ", name_model)
    # print("METHOD: ", method)
    result["from_aws"] = True
    method, task_params, error = get_method(current_obj)
    if method:
        try:
            new_tasks, final_errors, data = method(
                **result, task_params=task_params)
        except Exception:
            import traceback
            error_ = traceback.format_exc()
            print("ERROR EN EL MÉTODO: ", error_)
            final_errors.append(str(error_))
    else:
        print(error)
        final_errors.append(error)
    errors.extend(final_errors or [])
    current_task.date_end = datetime.now()
    return comprobate_status(current_task, errors, new_tasks)


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
        from task.models import AsyncTask

        # print("HOLA POST")
        # print(request)
        try:
            body = json.loads(request.body)
        except Exception as e:
            print("ERROR AL LEER EL BODY: ", e)
            print("request original: \n", request)
            return HttpResponse()
        # print("body: \n", body)
        special_function = body.get("special_function", {})
        if special_function:
            return calculate_special_function(special_function)
        request_id = body.get("request_id")
        # print("request_id: ", request_id)
        result = body.get("result", {})
        errors = result.get("errors", [])
        current_task = AsyncTask.objects.get(request_id=str(request_id))
        current_task.status_task_id = "success"
        current_task.date_arrive = datetime.now()
        # print("RESULT: ", result)
        current_task.result = result
        current_task.save()
        new_result = result.copy()
        function_after = current_task.function_after
        execute_function_aws(current_task, function_after, new_result, errors)

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
        # print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        # from task.models import AsyncTask
        print("HOLA ERRORES")
        # print(request)
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
                # current_task.errors = extract_only_message(error)
                current_task.traceback = request.body
                comprobate_status(current_task, error, [])
        except Exception as e:
            print("ERROR AL GUARDAR 1: ", e)
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


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def build_task_params(model, function_name, request, **kwargs):
    from datetime import datetime
    subgroup = kwargs.get("subgroup")
    parent_task = kwargs.get("parent_task")
    finished_function = kwargs.get("finished_function")
    # print("build_task_params 1: ", datetime.now())
    model_name = camel_to_snake(model.__class__.__name__)
    create_kwargs = {model_name: model}
    is_massive = bool(subgroup)

    def update_previous_tasks(tasks):
        # print("TASKS Previous: ", tasks)
        # tasks.update(is_current=False)
        for task in tasks:
            if task.is_current:
                task.is_current = False
                task.save()
            if task.child_tasks.exists():
                update_previous_tasks(task.child_tasks.all())

    if not is_massive:
        # print("build_task_params 2.0: ", datetime.now())
        update_previous_tasks(AsyncTask.objects.filter(**create_kwargs))
    # print("build_task_params 2.1: ", datetime.now())
    # print("function_name: ", function_name)
    if finished_function:
        create_kwargs["finished_function"] = finished_function
    if is_massive:
        create_kwargs["is_massive"] = True
        create_kwargs["subgroup"] = subgroup
    # print("build_task_params 3: ", datetime.now())
    task_function, created = TaskFunction.objects.get_or_create(
        name=function_name)
    if created:
        task_function.public_name = function_name
        task_function.save()
    # print("build_task_params 4: ", datetime.now())
    if model_name == "data_file":
        stage = task_function.stages.first()
        if stage:
            model.stage = stage
            model.status_id = "pending"
            model.save()
    # print("build_task_params 5: ", datetime.now())
    if parent_task:
        create_kwargs["parent_task"] = parent_task
    key_task = AsyncTask.objects.create(
        user=request.user, task_function=task_function,
        date_start=datetime.now(), status_task_id="created", **create_kwargs
    )
    # print("build_task_params 6: ", datetime.now())
    return key_task, {"parent_task": key_task}


def comprobate_status(
        current_task, errors=None, new_tasks=None, want_http_response=False):
    from rest_framework.response import Response
    from rest_framework import status
    if not current_task:
        raise Exception("No se ha encontrado la tarea enviada")
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
    comprobate_queue(current_task)
    return current_task


def execute_finished_function(parent_task):
    finished_function = parent_task.finished_function
    brothers_in_finish = AsyncTask.objects.filter(
        parent_task=parent_task,
        task_function_id=finished_function)
    if brothers_in_finish.exists():
        return "finished"
    else:
        params_after = parent_task.params_after or {}
        params_finished = params_after.get("params_finished", {})

        class RequestClass:
            def __init__(self):
                self.user = parent_task.user
        req = RequestClass()
        add_elems = {"parent_task": parent_task}
        model, current_obj = find_task_model(parent_task)
        new_task, task_params = build_task_params(
            current_obj, finished_function, req, **add_elems)
        new_task = execute_function_aws(
            new_task, finished_function, params_finished)
        is_final = new_task.status_task.is_completed
        parent_status_task_id = "finished" if is_final else "children_tasks"
    return parent_status_task_id


def comprobate_brothers(current_task, status_task_id):
    try:
        current_task = current_task.save_status(status_task_id)
    except Exception as e:
        print("current_task: ", current_task)
        print("ERROR AL GUARDAR: ", e)
    is_final = current_task.status_task.is_completed
    # print(current_task.id, " is_final: ", is_final)
    if is_final and current_task.parent_task:
        parent_task = current_task.parent_task
        brothers_incomplete = AsyncTask.objects.filter(
            parent_task=parent_task,
            status_task__is_completed=False)
        # print("paso por acá comprobando brothers")
        # print("brothers_incomplete: ", brothers_incomplete)
        if brothers_incomplete.exists():
            parent_status_task_id = "children_tasks"
        else:
            # print("finished_function: ", parent_task.finished_function)
            if parent_task.finished_function:
                parent_status_task_id = execute_finished_function(parent_task)
            else:
                # print("llego a finished del padre")
                parent_status_task_id = "finished"
        comprobate_brothers(parent_task, parent_status_task_id)
    return current_task


def comprobate_queue(current_task):
    from task.serverless import execute_async
    # from django.conf import settings
    # from inai.data_file_mixins.insert_mix import modify_constraints

    # is_queue = current_task.task_function_id in ["save_csv_in_db"]
    # if not is_queue:
    if not current_task.task_function.is_queueable:
        return
    if current_task.status_task.is_completed:
        next_task = AsyncTask.objects.filter(
            task_function_id=current_task.task_function_id,
            status_task_id="queue").order_by("id").first()
        if next_task:
            execute_async(next_task, next_task.original_request)
        # elif not settings.IS_LOCAL:
        #     modify_constraints(is_create=True)


def debug_queue():
    from task.serverless import execute_async
    # from inai.data_file_mixins.insert_mix import modify_constraints
    from datetime import timedelta
    from django.utils import timezone
    arrived_tasks = AsyncTask.objects.filter(
        status_task_id="success", task_function_id="save_csv_in_db")
    # arrived_tasks = AsyncTask.objects.filter(
    #     status_task_id="success", task_function__is_queueable=True)
    for task in arrived_tasks:
        if task.date_arrive + timedelta(seconds=5) < timezone.now():
            comprobate_status(task)
            errors = task.errors
            task.sheet_file.save_stage('transform', errors)
    every_completed = AsyncTask.objects.filter(
        status_task__is_completed=True,
        task_function__is_queueable=True)
    if every_completed.exists():
        next_task = AsyncTask.objects.filter(
            status_task_id="queue").order_by("id").first()
        if next_task:
            execute_async(next_task, next_task.original_request)
        # else:
        #     modify_constraints(is_create=True)
