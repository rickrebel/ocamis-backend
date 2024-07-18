
def find_task_model(async_task):
    task_models = [
        "petition", "file_control", "reply_file", "sheet_file",
        "data_file", "week_record", "month_record", "cluster",
        "mat_view"]
    for model in task_models:
        current_obj = getattr(async_task, model)
        if current_obj:
            return model, current_obj


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
