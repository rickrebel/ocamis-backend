
import psycopg2
from django.conf import settings


def upload_csv_to_database_prev(file_path, table_name, columns):
    f = open(file_path)
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))

    columns_join = ",".join(columns)
    options = "csv DELIMITER '|' NULL 'NULL' ENCODING 'LATIN1'"
    sql = "COPY %s(%s) FROM '%s\\%s' %s;" % (
        table_name, columns_join, base_dir, file_path, options)

    desabasto_conection = getattr(settings, "DATABASES").get("default")
    con = psycopg2.connect(
        database=desabasto_conection.get("NAME"),
        user=desabasto_conection.get("USER"),
        password=desabasto_conection.get("PASSWORD"),
        host=desabasto_conection.get("HOST"),
        port=desabasto_conection.get("PORT"))
    cur = con.cursor()
    try:
        cur.copy_expert(sql, f)
        # with open("%s_done" % file_path, 'wb') as file:
        #     file.write('done')
        # os.remove("%s\\%s" % (script_dir, origin_path))
    except Exception as e:
        print(e)
        con.close()
        f.close()
        return
    con.commit()
    con.close()
    f.close()
