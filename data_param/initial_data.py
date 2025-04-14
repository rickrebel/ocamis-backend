from data_param.models import Collection, FinalField, DataType


def field_of_models(collection: Collection):
    from django.apps import apps
    from django.db.models import CharField, TextField, IntegerField
    app_name = collection.app_label
    if not app_name:
        raise Exception("app_name is required")
    model_name = collection.model_name
    try:
        my_model = apps.get_model(app_name, model_name)
    except LookupError:
        print(f"Model {model_name} not found in app {app_name}")
        return
    all_fields = my_model._meta.get_fields(
        include_parents=False, include_hidden=False)

    data_types_dict = {dt.name: dt for dt in DataType.objects.all()}

    unique_names = set()
    for field in all_fields:
        if field.one_to_many:
            continue
        elif field.is_relation:
            continue
        elif field.primary_key:
            continue

        unique_names.add(field.name)
        try:
            ff = FinalField.objects.get(name=field.name, collection=collection)
        except FinalField.DoesNotExist:
            print(f"Field {field.name} not found in collection {collection}")
            continue
        except FinalField.MultipleObjectsReturned:
            print(f"Field {field.name} has multiple entries in collection {collection}")
            ff = FinalField.objects.filter(
                name=field.name, collection=collection).first()

        if isinstance(field, TextField):
            ff.data_type = data_types_dict["Text"]
        elif isinstance(field, CharField):
            ff.data_type = data_types_dict["Char"]
            addl_params = ff.addl_params or {}
            addl_params["max_length"] = field.max_length
            ff.addl_params = addl_params
        else:
            continue
        # ff.save()

    final_field_names = set(collection.final_fields.values_list("name", flat=True))
    for name in final_field_names:
        if name not in unique_names:
            print(f"Field {name} not found in model {model_name}")


def collections_in_app_label(app_label: str):
    # from django.apps import apps
    from data_param.models import Collection
    # my_app = apps.get_app_config(app_label)
    return Collection.objects.filter(app_label=app_label)


def main():
    apps = ["formula", "med_cat"]
    for app in apps:
        collections = collections_in_app_label(app)
        for collection in collections:
            print(f"--- {collection.model_name} ---")
            field_of_models(collection)

