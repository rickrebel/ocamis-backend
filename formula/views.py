from django.db import connection


def custom_constraint(constraint, year_month):
    constraint = constraint.replace(
        " on formula_", f" on fm_{year_month}_")
    constraint = constraint.replace(
        "alter table formula_", f" alter table fm_{year_month}_")
    constraint = constraint.replace(
        "references formula_", f"references fm_{year_month}_")
    clean_constraint = constraint.replace("\n", " \n")
    if "add constraint " in clean_constraint:
        original_constraint_name = clean_constraint.split(
            "add constraint ")[1].split(" ")[0]
    elif " exists " in clean_constraint:
        original_constraint_name = clean_constraint.split(
            " exists ")[1].split(" ")[0]
    else:
        raise Exception("Constraint name not found")
    constraint_name = original_constraint_name.replace("missingrow", "mr")
    constraint_name = constraint_name.replace("missingfield", "mf")
    constraint_name = constraint_name.replace("fk_formula", "fk_fm")
    constraint_name = constraint_name.replace("formula_", f"fm_{year_month}_")
    return clean_constraint.replace(original_constraint_name, constraint_name)


def modify_constraints(is_create=True, is_rebuild=False, year_month=None):
    from task.models import Platform
    from scripts.verified.indexes.constrains import get_constraints
    from datetime import datetime
    create_constrains, delete_constrains = get_constraints(is_rebuild)
    if is_rebuild:
        return
    with_change = False
    cursor = connection.cursor()
    print("START", datetime.now())
    valid_strings = [" on TABLE ", " table TABLE ", " index if exists TABLE"]
    valid_tables = ["rx", "drug", "missingrow", "missingfield",
                    "complementrx", "complementdrug"]
    invalid_fields = ["lap_sheet_id", "sheet_file_id", "_like"]
    constraint_list = create_constrains if is_create \
        else reversed(delete_constrains)
    new_constraints = []
    # and platform.has_constrains:
    print("is_create", is_create)
    for constraint in constraint_list:
        valid_constraint = not bool(year_month)
        for valid_string in valid_strings:
            for valid_table in valid_tables:
                final_valid_string = valid_string.replace(
                    "TABLE", f"formula_{valid_table}")
                if final_valid_string in constraint:
                    valid_constraint = True
        if is_create and valid_constraint:
            for invalid_field in invalid_fields:
                if invalid_field in constraint:
                    valid_constraint = False
        if not valid_constraint:
            continue
        try:
            if year_month:
                constraint = custom_constraint(constraint, year_month)
                # print("final_constraint:", constraint)
                new_constraints.append(constraint)
            else:
                print(">>>>> time:", datetime.now())
                print("constraint:", constraint)
                cursor.execute(constraint)
                print("--------------------------")
            # if "formula_rx_pkey" in constraint:
            #     rebuild_primary_key(cursor, "formula_rx", constraint)
            # else:
            #     cursor.execute(constraint)
        except Exception as e:
            str_e = str(e)
            if "already exists" in str_e:
                continue
            if "multiple primary keys" in str_e:
                continue
            print("constraint", constraint)
            print(f"ERROR:\n, {e}, \n--------------------------")
            raise e
    # connection.commit()
    print("FINAL", datetime.now())
    cursor.close()
    connection.close()
    if year_month:
        return new_constraints
    elif with_change:
        Platform.objects.all().update(has_constrains=is_create)


# modify_constraints(True, False, "55_201902")
# modify_constraints(False, False, "55_201701")


def rebuild_primary_key(cursor, table_name, constraint):
    from inai.models import WeekRecord
    from task.models import AsyncTask
    from task.serverless import execute_async
    from django.utils import timezone
    fields = [
        "provider_id", "iso_year", "month", "iso_week", "iso_delegation",
        "month", "year"]
    try:
        cursor.execute(constraint)
    except Exception as e:
        str_e = str(e)
        # Key (uuid_folio)=(d0c82080-f73e-4cf7-9e65-557c6ecfa64b) is duplicated.
        if "is duplicated" in str_e and "Key (uuid_folio)" in str_e:
            value = str_e.split("Key (uuid_folio)=(")[1].split(")")[0]
            print("value", value)
            print("time_now", timezone.now())
            query_duplicates = f"""
                SELECT {", ".join(fields)} 
                 FROM {table_name} WHERE uuid_folio = '{value}'
                 LIMIT 1;
            """
            print("query_duplicates", query_duplicates)
            cursor.execute(query_duplicates)
            result = cursor.fetchone()
            get_params = {field: result[i] for i, field in enumerate(fields)}
            week_record = WeekRecord.objects.get(**get_params)
            print("time_now", timezone.now())
            print("week_record", week_record)
            complement_delete_rx = [f"{field} = {result[i]}"
                                    for i, field in enumerate(fields)]
            query_delete_rx = f"""
                DELETE FROM formula_rx WHERE {" AND ".join(complement_delete_rx)};
            """
            print("query_delete_rx", query_delete_rx)
            cursor.execute(query_delete_rx)
            print("time_now", timezone.now())
            complement_delete_drug = f"""
                DELETE FROM formula_drug WHERE week_record_id = {week_record.id}
            """
            print("complement_delete_drug", complement_delete_drug)
            cursor.execute(complement_delete_drug)
            print("time_now", timezone.now())
            # last_insertion = week_record.last_insertion
            week_record.last_pre_insertion = None
            week_record.save()
            task = AsyncTask.objects.filter(
                week_record=week_record,
                task_function_id='save_week_base_models')
            if task.exists():
                task = task.first()
                new_task = task
                new_task.pk = None
                new_task.save()
                new_task.status_task_id = "queue"
                new_task.result = None
                new_task.errors = None
                new_task.date_start = timezone.now()
                new_task.date_arrive = None
                new_task.date_end = None
                new_task.save()
                execute_async(new_task, new_task.original_request)
            rebuild_primary_key(cursor, table_name, constraint)
            # raise "MADA"
        else:
            raise e
