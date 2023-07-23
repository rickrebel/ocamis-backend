from django.db import connection


def rebuild_primary_key(cursor, table_name, constraint):
    from inai.models import EntityWeek
    from task.models import AsyncTask
    from task.serverless import execute_async
    from django.utils import timezone
    fields = [
        "entity_id", "iso_year", "month", "iso_week", "iso_delegation",
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
            entity_week = EntityWeek.objects.get(**get_params)
            print("time_now", timezone.now())
            print("entity_week", entity_week)
            complement_delete_rx = [f"{field} = {result[i]}"
                                    for i, field in enumerate(fields)]
            query_delete_rx = f"""
                DELETE FROM formula_rx WHERE {" AND ".join(complement_delete_rx)};
            """
            print("query_delete_rx", query_delete_rx)
            cursor.execute(query_delete_rx)
            print("time_now", timezone.now())
            complement_delete_drug = f"""
                DELETE FROM formula_drug WHERE entity_week_id = {entity_week.id}
            """
            print("complement_delete_drug", complement_delete_drug)
            cursor.execute(complement_delete_drug)
            print("time_now", timezone.now())
            # last_insertion = entity_week.last_insertion
            entity_week.last_insertion = None
            entity_week.save()
            task = AsyncTask.objects.filter(
                entity_week=entity_week, task_function_id='save_csv_in_db')
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


def modify_constraints(is_create=True, is_rebuild=False):
    from task.models import Platform
    from scripts.ocamis_verified.constrains import get_constraints
    from datetime import datetime
    create_constrains, delete_constrains = get_constraints(is_rebuild)
    if is_rebuild:
        return
    with_change = False
    cursor = connection.cursor()
    print("START", datetime.now())
    if is_create:  # and not platform.has_constrains:
        print("create_constrains")
        with_change = True
        for constraint in create_constrains:
            try:
                print(">>>>> time:", datetime.now())
                print("constraint", constraint)
                if "formula_rx_pkey" in constraint:
                    rebuild_primary_key(cursor, "formula_rx", constraint)
                else:
                    cursor.execute(constraint)
                print("--------------------------")
            except Exception as e:
                str_e = str(e)
                if "already exists" in str_e:
                    continue
                if "multiple primary keys" in str_e:
                    continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                raise e
    elif not is_create:  # and platform.has_constrains:
        print("delete_constrains")
        with_change = True
        for constraint in reversed(delete_constrains):
            print("constraint", constraint)
            cursor.execute(constraint)
    # connection.commit()
    print("FINAL", datetime.now())
    cursor.close()
    connection.close()
    if with_change:
        Platform.objects.all().update(has_constrains=is_create)
