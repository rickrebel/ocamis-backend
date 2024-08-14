
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

    def execute_many_queries(self, queries, need_raise=True):
        for query in queries:
            self.execute_query(query, need_raise=False)
        if self.errors and need_raise:
            raise self.errors

    def execute_query(self, query_content, need_raise=True, error_msg=None):
        try:
            self.cursor.execute(query_content)
            if error_msg:
                result = self.cursor.fetchone()
                if result[0]:
                    self.errors.append(error_msg)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            self.errors.append(
                f"Hubo un error al guardar; \n{query_content}; \n{str(e)}")
            if need_raise:
                raise self.errors

    def constraint_queries(self, constraint_queries):
        valid_errors = [
            "already exists", "ya existe",
            "multiple primary keys", "tiples llaves primarias",
            "current transaction is aborted",
            "la transacción actual ha sido abortada",
            "no existe la relación"
        ]
        for constraint in constraint_queries:
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
                    f"Error en constraint {constraint}; --> {str_e} <--")
                raise self.errors

    def comprobate_errors(self):
        if self.errors:
            self.connection.rollback()
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



