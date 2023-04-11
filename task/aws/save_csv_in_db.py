
# def save_csv_in_db(event, context):
def lambda_handler(event, context):
    import psycopg2
    db_config = event.get("db_config")
    sql_queries = event.get("sql_queries")
    connection = psycopg2.connect(
        database=db_config.get("NAME"),
        user=db_config.get("USER"),
        password=db_config.get("PASSWORD"),
        host=db_config.get("HOST"),
        port=db_config.get("PORT"))
    cursor = connection.cursor()
    for sql_query in sql_queries:
        cursor.execute(sql_query)
    connection.commit()
    cursor.close()
    connection.close()
