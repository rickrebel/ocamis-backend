
def create_connection(db_config):
    import psycopg2
    connection = psycopg2.connect(
        database=db_config.get("NAME"),
        user=db_config.get("USER"),
        password=db_config.get("PASSWORD"),
        host=db_config.get("HOST"),
        port=db_config.get("PORT"))
    return connection


class QueryExecution:

    def __init__(self, event, context):
        self.event = event
        self.connection = create_connection(event.get("db_config"))
        self.cursor = self.connection.cursor()
        self.errors = []
        self.warnings = []

    def execute_many_queries(self, queries, need_raise=True, need_sleep=False):
        import time
        if need_sleep:
            time.sleep(0.5)
        for query in queries:
            if need_sleep:
                time.sleep(0.5)
            self.execute_query(query, need_raise=False)
        if need_sleep:
            time.sleep(0.5)
        if self.errors and need_raise:
            raise self.errors

    def execute_query(self, query_content, need_raise=True, error_msg=None,
                      is_soft=False):
        try:
            self.cursor.execute(query_content)
            if error_msg:
                result = self.cursor.fetchone()
                if result[0]:
                    if is_soft:
                        print(f"SOFT ERROR: {error_msg}")
                    else:
                        self.errors.append(error_msg)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            if "0 rows were copied successfully" in str_e and "diagnosisrx" in query_content:
                return
            self.errors.append(
                f"$ Hubo un error al guardar; \n{query_content}; \n{str(e)}")
            if need_raise:
                raise self.errors

    def constraint_queries(self, constraint_queries):
        import time
        valid_errors = [
            "already exists", "ya existe",
            "multiple primary keys", "tiples llaves primarias",
            "current transaction is aborted",
            "la transacción actual ha sido abortada",
            "no existe la relación"
        ]
        for constraint in constraint_queries:
            if "table_import_from_s3" in constraint:
                time.sleep(3)
            # print("before constraint_query", datetime.now())
            try:
                self.cursor.execute(constraint)
            except Exception as e:
                str_e = str(e)
                # for valid_error in valid_errors:
                #     if valid_error in str_e:
                #         continue
                if any([valid_error in str_e for valid_error in valid_errors]):
                    print(f"str_e en constraint {constraint}", str_e)
                    continue
                # print("constraint", constraint)
                # print(f"ERROR:\n, {e}, \n--------------------------")
                self.errors.append(
                    f"Error en constraint: {constraint}; --> {str_e} <--")
                raise self.errors

    def _update_table_files(self, table_files_ids):
        str_table_files_ids = [str(x) for x in table_files_ids]
        query = f"UPDATE inai_tablefile SET inserted = true " \
                f"WHERE id IN ({','.join(str_table_files_ids)})"
        self.execute_query(query)

    def add_error_and_raise(self, error):
        self.errors.append(error)
        self.comprobate_errors()

    def comprobate_errors(self):
        if self.errors:
            raise self.errors

    def rollback(self):
        self.connection.rollback()
        self.close()

    def finish_and_save(self):
        self.cursor.close()
        self.connection.commit()
        self.close()

    def close(self):
        self.connection.close()
        self.errors.extend(self.warnings)
