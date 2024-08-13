from django.db import connection
from rds.models import Cluster, Stage, MatView, Operation
from django.conf import settings


class ConstraintBuilder:

    def __init__(self, is_create=True, prov_year_month=None, group='month',
                 cluster=None):
        self.is_create = is_create
        self.prov_year_month = prov_year_month
        self.group = group
        self.cursor = None

        self.cluster = cluster
        self.mat_view = None
        self.mat_name = None
        self.file_path = None

        if not self.prov_year_month:
            self.cursor = connection.cursor()
        self.valid_strings = [
            " on TABLE ", " table TABLE ", " index if not exists TABLE"]
        self.valid_tables = [
            "rx", "drug", "missingrow", "missingfield", "complementrx",
            "complementdrug", "diagnosisrx"]
        self.invalid_fields = ["lap_sheet_id", "sheet_file_id", "_like"]
        self.new_constraints = []
        if self.group == "month":
            self.schema = "tmp"
            self.abbrev = "fm"
        elif self.group == "cluster":
            self.schema = "base"
            self.abbrev = "frm"
        else:
            self.schema = "public"
            self.abbrev = "formula"
        # self.schema = "tmp" if self.group == "month" else "public"
        # self.abbrev = "fm" if self.schema == "tmp" else "frm"
        self.init_table_name = f"{self.schema}.{self.abbrev}_{self.prov_year_month}"
        self.constraint = None

    def mat_view_queries(self, mat_view: MatView):
        from task.serverless import camel_to_snake

        self.mat_view = mat_view
        snake_name = camel_to_snake(mat_view.name)
        self.mat_name = f"{self.init_table_name}_{snake_name}"
        base_path_name = self.mat_name.replace("base.", "")
        self.file_path = f"mat_views/{self.cluster.name}/{base_path_name}.csv"
        return [
            {"name": "create", "script": self.custom_mat_view(mat_view)},
            {"name": "save", "script": self.save_mat_view_in_s3()},
            {"name": "copy", "script": self.query_to_copy_export(snake_name)}]

    def custom_mat_view(self, mat_view):
        main_field = "script" if self.is_create else "drop_script"
        script = getattr(mat_view, main_field)
        script = script.replace(";", "")
        script = script.replace("CLUSTER_NAME", self.cluster.name)
        script = script.replace(" formula_", f" {self.init_table_name}_")
        init_script = "CREATE MATERIALIZED VIEW" if self.is_create \
                      else "DROP MATERIALIZED VIEW"
        return (f"{init_script} {self.mat_name} AS"
                f"\n{script}\n    WITH DATA;")

    def save_mat_view_in_s3(self):
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        region_name = getattr(settings, "AWS_S3_REGION_NAME")
        return f"""
        SELECT aws_s3.query_export_to_s3(
            'SELECT * FROM {self.mat_name}',
            aws_commons.create_s3_uri('{bucket_name}', '{self.file_path}', '{region_name}'),
            options := 'format csv, delimiter ''|'', header true'
        );
        """

    def query_to_copy_export(self, snake_name):
        from respond.data_file_mixins.matches_mix import field_of_models
        from inai.misc_mixins.insert_month_mix import build_copy_sql_aws

        columns = field_of_models({"model": snake_name, "app": "formula"})
        column_names = [column["name"] for column in columns]
        columns_join = ",".join(column_names)
        model_name = f"public.{snake_name}"
        return build_copy_sql_aws(self.file_path, model_name, columns_join)

    def modify_constraints(self):
        from rds.models import Operation
        from datetime import datetime
        main_field = "script" if self.is_create else "drop_script"
        order_by = "order" if self.is_create else "-order"
        q_filter = {
            "operation_type__in": ["constraint", "index"],
            "is_active": True}
        if self.group == "cluster":
            q_filter["low_priority"] = False
        # constraint_list = Operation.objects\
        operations = Operation.objects\
            .filter(**q_filter)\
            .order_by(order_by)
        # .values_list(main_field, flat=True)
        # print("START", datetime.now())
        for operation in operations:
            constraint = getattr(operation, main_field)
            constraint = constraint.replace("\n", " \n")
            valid_constraint = not bool(self.prov_year_month)
            for valid_string in self.valid_strings:
                for valid_table in self.valid_tables:
                    final_valid_string = valid_string.replace(
                        "TABLE", f"formula_{valid_table}")
                    if final_valid_string in constraint:
                        valid_constraint = True
            if self.is_create and valid_constraint:
                for invalid_field in self.invalid_fields:
                    if invalid_field in constraint:
                        valid_constraint = False
            if not valid_constraint:
                print("invalid_constraint", constraint, "\n\n")
                continue

            try:
                self.constraint = constraint
                self.custom_constraint()
                self.new_constraints.append((self.constraint, operation))

            except Exception as e:
                str_e = str(e)
                if "already exists" in str_e:
                    continue
                if "multiple primary keys" in str_e:
                    continue
                print("constraint", constraint)
                print(f"ERROR:\n, {e}, \n--------------------------")
                raise e
        print("FINAL", datetime.now())
        if not self.prov_year_month:
            self.cursor.close()
            connection.close()
        if self.prov_year_month:
            return self.new_constraints

    def custom_constraint(self):
        from datetime import datetime
        if not self.prov_year_month:
            print(">>>>> time:", datetime.now())
            print("constraint:", self.constraint)
            self.cursor.execute(self.constraint)
            print("--------------------------")
            return

        replaces = [
            (" on formula_", f" on {self.init_table_name}_"),
            ("alter table formula_", f" alter table {self.init_table_name}_"),
            ("\n", " \n")]
        special_replaces = [
            ("references formula_", f"references {self.init_table_name}_"),
            # ("references ", f"references {self.schema}.")]
            ("references ", f"references public.")]

        def run_replace(original, replace):
            self.constraint = self.constraint.replace(original, replace)

        for replace in special_replaces:
            if replace[0] in self.constraint:
                run_replace(*replace)
                break
        for replace in replaces:
            run_replace(*replace)

        if "add constraint " in self.constraint:
            split_txt = "add constraint "
        elif " exists " in self.constraint:
            split_txt = " exists "
        else:
            raise Exception("Constraint name not found")
        original_name = self.constraint.split(split_txt)[1].split(" ")[0]
        name_replaces = [
            ("missingrow", "mr"),
            ("missingfield", "mf"),
            ("fk_formula", "fk_fm"),
            ("formula_", f"{self.abbrev}_{self.prov_year_month}_")]
        new_constraint_name = original_name
        for replace in name_replaces:
            new_constraint_name = new_constraint_name.replace(*replace)
        self.constraint = self.constraint.replace(
            original_name, new_constraint_name)
        if len(new_constraint_name) > 63:
            self.constraint = self.constraint[:63]


def custom_constraint(constraint, prov_year_month, schema="tmp"):
    abbrev = "fm" if schema == "tmp" else "frm"
    init_table_name = f"{schema}.{abbrev}_{prov_year_month}"
    constraint = constraint.replace(
        " on formula_", f" on {init_table_name}_")
    constraint = constraint.replace(
        "alter table formula_", f" alter table {init_table_name}_")
    if "references formula_" in constraint:
        constraint = constraint.replace(
            "references formula_", f"references {init_table_name}_")
    elif "references " in constraint:
        constraint = constraint.replace(
            "references ", f"references public.")
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
    constraint_name = constraint_name.replace("formula_", f"fm_{prov_year_month}_")
    return clean_constraint.replace(original_constraint_name, constraint_name)


def modify_constraints(
        is_create=True, is_rebuild=False, prov_year_month=None):
    from scripts.verified.indexes.constrains import get_constraints
    from datetime import datetime
    if is_rebuild:
        get_constraints(is_rebuild)
        return

    # create_constrains, delete_constrains = get_constraints(is_rebuild)
    main_field = "script" if is_create else "drop_script"
    order_by = "order" if is_create else "-order"
    constraint_list = Operation.objects\
        .filter(operation_type__in=["constraint", "index"], is_active=True)\
        .order_by(order_by)\
        .values_list(main_field, flat=True)
    # with_change = False
    cursor = connection.cursor()
    print("START", datetime.now())
    valid_strings = [" on TABLE ", " table TABLE ", " index if exists TABLE"]
    valid_tables = ["rx", "drug", "missingrow", "missingfield",
                    "complementrx", "complementdrug", "diagnosisrx"]
    invalid_fields = ["lap_sheet_id", "sheet_file_id", "_like"]
    # constraint_list = create_constrains if is_create \
    #     else reversed(delete_constrains)
    new_constraints = []
    # and platform.has_constrains:
    print("is_create", is_create)
    for constraint in constraint_list:
        valid_constraint = not bool(prov_year_month)
        for valid_string in valid_strings:
            for valid_table in valid_tables:
                final_valid_string = valid_string.replace(
                    "TABLE", f"formula_{valid_table}")
                # print(f"final_valid_string >{final_valid_string}<")
                if final_valid_string in constraint:
                    # print("valid_constraint", constraint)
                    valid_constraint = True
        if is_create and valid_constraint:
            for invalid_field in invalid_fields:
                if invalid_field in constraint:
                    valid_constraint = False
        if not valid_constraint:
            print("invalid_constraint:\n", constraint, "\n\n")
            continue
        try:
            if prov_year_month:
                constraint = custom_constraint(constraint, prov_year_month)
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
    if prov_year_month:
        return new_constraints
    # elif with_change:
    #     Platform.objects.all().update(has_constrains=is_create)


# modify_constraints(True, False, "55_201902")
# modify_constraints(False, False, "55_201701")


def rebuild_primary_key(cursor, table_name, constraint):
    from inai.models import WeekRecord
    from task.models import AsyncTask
    # from task.serverless import execute_async
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
                # execute_async(new_task, new_task.original_request)
            # rebuild_primary_key(cursor, table_name, constraint)
            # raise "MADA"
        else:
            raise e
