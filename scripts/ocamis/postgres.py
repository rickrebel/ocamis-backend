from formula.models import Drug, Rx, MissingRow, MissingField


def delete_indexes_by_model(model):
    from django.db import connection
    cursor = connection.cursor()
    table_name = model._meta.db_table
    # ALTER TABLE {model._meta.db_table} DISABLE TRIGGER ALL
    sql_query = f"""
        SELECT indexname FROM pg_indexes WHERE tablename = '{table_name}';
    """
    cursor.execute(sql_query)
    result = []
    all_indexes = cursor.fetchall()
    for index in all_indexes:
        for index_name in index:
            result.append(index_name)
            sql_query = f"""
                DROP INDEX {index_name};
            """
            cursor.execute(sql_query)
    cursor.close()
    connection.close()
    return result


def delete_constrains_by_model(model):
    from django.db import connection
    cursor = connection.cursor()
    table_name = model._meta.db_table
    # ALTER TABLE {model._meta.db_table} DISABLE TRIGGER ALL
    sql_query = f"""
        SELECT conname, conrelid::regclass, contype
        FROM pg_constraint
        WHERE conrelid = '{table_name}'::regclass;
    """
    cursor.execute(sql_query)
    result = []
    all_constrains = cursor.fetchall()
    for constrain in all_constrains:
        for constrain_name in constrain:
            result.append(constrain_name)
            sql_query = f"""
                ALTER TABLE {table_name} DROP CONSTRAINT {constrain_name};
            """
            cursor.execute(sql_query)
    cursor.close()
    connection.close()
    return result


def delete_all_indexes_and_constrains():
    models = [Drug, Rx, MissingRow, MissingField]
    for model in models:
        delete_indexes_by_model(model)
        delete_constrains_by_model(model)
