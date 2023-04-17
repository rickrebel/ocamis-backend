import io
from task.models import Platform
from django.apps import apps
from django.db.models import Index
from django.db import connection


def build_constraints_and_indexes(use_complement=False):
    file_sql = 'scripts/ocamis_verified/ddl_editables.sql'
    complement_path = "C:/Users/Ricardo/dev/desabasto/desabasto-api/"
    final_path = f"{complement_path}{file_sql}" if use_complement else file_sql
    print(final_path)
    try:
        with io.open(final_path, "r", encoding="utf-8") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        if not use_complement:
            print("HOLA MUNDO")
            return build_constraints_and_indexes(use_complement=True)
        return [], []
    rr_data_rows = data.split("\n")
    last_table = None
    create_commands = []
    delete_commands = []
    last_commands = []
    last_function = None
    last_field = None
    current_command = None
    def add_block(commands):
        block = "\n".join(commands)
        create_commands.append(block)
    def add_delete_block(block):
        delete_commands.append(block)
    for row in rr_data_rows:
        constraint_name = None
        if not row or "alter table" in row or "owner to" in row:
            last_function = None
            last_field = None
            last_table = None
            continue
        if row == "(":
            continue
        if row == ");":
            if last_commands:
                last_commands[-1] = last_commands[-1].replace(",", "")
                last_commands[-1] = f"{last_commands[-1]};"
                add_block(last_commands)
            last_commands = None
            current_command = None
            last_function = None
            last_field = None
            last_table = None
            continue
        like_comma = "," in row
        if "create table " in row:
            last_table = row.split("public.")[1]
            if "formula" not in last_table and "med_cat" not in last_table:
                last_table = None
                # last_model = None
                continue
            # last_model = Collection.objects.get(name_in_db=last_table)
            last_commands = [f"alter table public.{last_table}"]
            continue
        elif not last_table:
            if "create index" in row:
                last_function = "index"
                index_name = row.split("index if not exists ")[1]
                # print("index_name:", index_name)
                if "formula_" not in index_name and "med_cat_" not in index_name:
                    last_function = None
                    continue
                last_commands = [f"create index if not exists {index_name}"]
                delete_command = f"drop index if exists {index_name}"
                add_delete_block(delete_command)
                continue
            elif "on public." in row and last_function == "index":
                print("on public.:", row)
                current_command = f"   on {row.split('on ', 1)[1]}"
                last_commands.append(current_command)
                add_block(last_commands)
                last_function = None
                current_command = None
                last_commands = None
            continue
        if "constraint" in row:
            constraint_name = row.split("constraint ")[1]
            current_command = f"add constraint {constraint_name}"
            # last_commands = "\n".join([last_commands, current_command])
            last_function = "constraint"
        elif last_function == "constraint":
            if "primary key" in row:
                current_command = f"   primary key ({last_field})"
                like_comma = True
            if "references" in row:
                current_command = f"   foreign key ({last_field})"
                current_command += f" references {row.split('references ')[1]}"
            elif "check" in row or "deferrable" in row:
                current_command = row
        elif "primary key" in row:
            last_function = "primary key"
            constraint_name = f"{last_table}_pkey"
            current_command = f"add constraint {constraint_name} \n" \
                              f" primary key ({last_field})"
        else:
            row_strip = row.strip()
            last_field = row_strip.split(" ")[0]
            print("last_field:", last_field)
            print("row", row, "\n")
        if current_command:
            current_command = current_command.replace(",", "")
            if like_comma:
                current_command = f"{current_command},"
            last_commands.append(current_command)
        if like_comma:
            last_field = None
            last_function = None
            current_command = None
        if constraint_name:
            delete_command = f"alter table public.{last_table} " \
                             f"drop constraint if exists {constraint_name};"
            add_delete_block(delete_command)
    return create_commands, delete_commands


def get_constraints(rebuild=False):
    platform = Platform.objects.all().first()
    first_time = False
    if not platform:
        platform = Platform.objects.create(version="2.3")
        first_time = True
    if rebuild or first_time:
        create_constrains, delete_constrains = build_constraints_and_indexes()
        platform.create_constraints = create_constrains
        platform.delete_constraints = delete_constrains
        platform.save()
    return platform.create_constraints, platform.delete_constraints


def create_constraints_and_indexes(model_name, app_label):
    # _model_indexes_sql

    model = apps.get_model(app_label, model_name)
    schema_editor = connection.schema_editor()
    print("------------------")
    print("MODEL:", model, model_name, app_label)
    with schema_editor.connection.cursor() as cursor:
        schema_editor.deferred_sql = []  # Clear any deferred SQL from previous operations

        real_model_name = f"{app_label}_{model_name.lower()}"
        primary_key_field = model._meta.pk
        primary_key_name = f"{real_model_name}_pkey"
        schema_editor.execute(
            schema_editor.sql_create_pk % {
                "table": schema_editor.quote_name(model._meta.db_table),
                "name": schema_editor.quote_name(primary_key_name),
                "columns": schema_editor.quote_name(primary_key_field.column),
            }
        )

        for field in model._meta.get_fields():
            print("FIELD:", field)
            try:
                print("db_constraint:", field.db_constraint)
            except Exception as e:
                print(e)
                continue
            if field.remote_field and field.db_constraint:
                schema_editor.execute(schema_editor._create_fk_sql(
                    model, field, '_fk_%(to_table)s_%(to_column)s'))
                index_name = schema_editor._create_index_name(
                    real_model_name, [field.column])
                temp_index = Index(
                    fields=[field.name],
                    name=index_name)
                schema_editor.execute(schema_editor._create_index_sql(
                    model, fields=[field], name=temp_index.name))
        alter_statements = schema_editor.deferred_sql

    return alter_statements


def delete_constraints_and_indexes(model_name, app_label):
    model = apps.get_model(app_label, model_name)
    print("------------------")
    print("MODEL:", model, model_name, app_label)
    schema_editor = connection.schema_editor()
    with schema_editor.connection.cursor() as cursor:
        real_model_name = f"{app_label}_{model_name.lower()}"
        schema_editor.deferred_sql = []  # Clear any deferred SQL from previous operations
        try:
            schema_editor.execute(schema_editor._delete_index_sql(
                model, "hex_hash"))
        except Exception as e:
            pass
        real_model_name = f"{app_label}_{model_name.lower()}"
        primary_key_field = model._meta.pk
        primary_key_name = f"{real_model_name}_pkey"
        try:
            schema_editor.execute(
                schema_editor.sql_delete_pk % {
                    "table": schema_editor.quote_name(model._meta.db_table),
                    "name": schema_editor.quote_name(primary_key_name),
                }
            )
        except Exception as e:
            print(e)
        all_constraints = schema_editor._constraint_names(model)
        for constraint_name in all_constraints:
            try:
                schema_editor.execute(schema_editor._delete_check_sql(
                    model, constraint_name))
            except Exception as e:
                print(e)
        for field in model._meta.get_fields(
                include_parents=False, include_hidden=False):
            # print("FIELD:", field)
            try:
                print("db_constraint:", field.db_constraint)
            except Exception as e:
                # print(e)
                continue
            is_index = schema_editor._field_should_be_indexed(
                model, field)
            if is_index:
                index_name = schema_editor._create_index_name(
                    real_model_name, [field.column])
                schema_editor.execute(schema_editor._delete_index_sql(
                    model, index_name))
        alter_statements = schema_editor.deferred_sql

    return alter_statements


def modify_constraints_prev(create=True):
    all_models = [
        {"model": "MissingField", "order": 0, "app": "formula"},
        {"model": "MissingRow", "order": 1, "app": "formula"},
        {"model": "Drug", "order": 2, "app": "formula"},
        {"model": "Prescription", "order": 3, "app": "formula"},
        {"model": "Delivered", "order": 4, "app": "med_cat"},
        {"model": "Doctor", "order": 5, "app": "med_cat"},
        {"model": "MedicalUnit", "order": 6, "app": "med_cat"},
        {"model": "Area", "order": 7, "app": "med_cat"},
        {"model": "Medicament", "order": 8, "app": "med_cat"},
        {"model": "Diagnosis", "order": 9, "app": "med_cat"},
    ]
    all_models = sorted(
        all_models, key=lambda k: -k["order"] if create else k["order"])
    for model in all_models:
        if create:
            create_constraints_and_indexes(model["model"], model["app"])
        else:
            delete_constraints_and_indexes(model["model"], model["app"])
    if not create:
        for model in all_models:
            delete_constraints_and_indexes(model["model"], model["app"])
    Platform.objects.all().update(has_constrains=create)


