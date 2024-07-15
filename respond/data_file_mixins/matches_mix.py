from data_param.models import Transformation
from scripts.common import start_session, create_file
import json
from task.base_views import TaskBuilder
from task.serverless import camel_to_snake
from respond.models import DataFile, LapSheet
from respond.data_file_mixins.base_transform import BaseTransform


def get_models_of_app(app_label):
    from django.apps import apps
    from data_param.models import Collection
    app = apps.get_app_config(app_label)
    models = app.get_models()
    all_models = []
    collection_models = Collection.objects\
        .filter(app_label=app_label)\
        .values_list('model_name', flat=True)
    for model in models:
        model_name = model.__name__
        if model_name not in collection_models:
            continue
        if model_name == 'Delivered':
            continue
        all_models.append({
            'app': app_label,
            'model': model_name,
            'name': camel_to_snake(model_name),
            "model_in_db": f"{app_label}_{model_name.lower()}",
        })
    return all_models


def get_name_in_data(column):
    return column.name_in_data or \
        f"en posición {column.position_in_data}"


def field_of_models(model_data):
    from django.apps import apps
    from django.db.models import CharField, TextField
    app_name = model_data.get('app')
    if not app_name:
        raise Exception("app_name is required")
    model_name = model_data['model']
    my_model = apps.get_model(app_name, model_name)
    all_fields = my_model._meta.get_fields(
        include_parents=False, include_hidden=False)
    fields = []
    for field in all_fields:
        if field.one_to_many:
            continue
        complement = "_id" if field.is_relation else ""
        field_name = f"{field.name}{complement}"
        is_char = isinstance(field, CharField)
        is_string = isinstance(field, TextField) or is_char
        fields.append({
            "name": field_name,
            "is_string": is_string,
            "is_relation": field.is_relation,
            "max_length": field.max_length if is_char else None,
        })
    return fields


def build_global_geo(global_obj):
    if not global_obj:
        return None
    is_clues = global_obj.__class__.__name__ == "CLUES"
    final_dict = {"id": global_obj.id}
    if is_clues:
        # is_tuple = isinstance(global_obj.clues, tuple)
        final_dict["clues_key"] = global_obj.clues
    else:
        final_dict["name"] = global_obj.name,
    return final_dict


def build_available_deliveries():
    from med_cat.models import Delivered
    all_deliveries = Delivered.objects.filter(
        alternative_names__isnull=False)
    deliveries = {}
    for delivery in all_deliveries:
        current_deliveries = delivery.alternative_names.split(",")
        for current_delivery in current_deliveries:
            delivered_name = current_delivery.strip().upper()
            deliveries[delivered_name] = delivery.hex_hash
    return deliveries


class MatchTransform(BaseTransform):

    def __init__(self, data_file: DataFile, task_params=None,
                 base_task: TaskBuilder = None):
        super().__init__(data_file, task_params)
        from inai.models import set_upload_path
        from data_param.models import NameColumn
        self.lap = self.data_file.next_lap
        petition = data_file.petition_file_control.petition

        self.provider = petition.real_provider or petition.agency.provider
        self.institution = self.provider.institution
        self.global_clues = self.provider.ent_clues.first() if self.provider.is_clues else None
        # print("self.institution.code", self.institution.code)
        self.global_delegation = self.global_clues.delegation \
            if self.global_clues else None
        # print("global_delegation", self.global_delegation)
        # only_name = f"NEW_ELEM_NAME/{self.data_file.id}_SHEET_NAME_lap{self.lap}.csv"
        file_name = self.file_name
        only_name = f"NEW_ELEM_NAME/{file_name}_SHEET_NAME_NEW_ELEM_NAME" \
                    f"_lap{self.lap}.csv"
        self.final_path = set_upload_path(self.data_file, only_name)
        self.name_columns = NameColumn.objects \
            .filter(file_control=self.file_control) \
            .prefetch_related(
                "final_field",
                "final_field__collection",
                "final_field__parameter_group",
                "column_transformations",
                "column_transformations__clean_function",
            )

        original_columns = self.name_columns.filter(
            position_in_data__isnull=False)
        self.delimiter = self.file_control.delimiter

        self.columns_count = original_columns.count()

        self.editable_models = get_models_of_app("med_cat")
        self.editable_models += get_models_of_app("formula")
        self.real_models = list(set(self.name_columns.values_list(
            "final_field__collection__model_name", flat=True)))
        self.model_fields = {model["name"]: field_of_models(model)
                             for model in self.editable_models}

        self.existing_fields = []
        self.task_params = task_params

        # s3_client, dev_resource = start_session()
        # self.s3_client = s3_client

    def build_init_data(self, final_lap, string_date):
        from geo.views import build_catalog_delegation_by_id
        import hashlib

        value_null = "".encode(self.file_control.decode or "utf-8")
        hash_null = hashlib.md5(value_null).hexdigest()
        global_transformations = self.file_control.file_transformations \
            .values_list("clean_function__name", flat=True)
        global_transformations = list(global_transformations)

        init_data = {
            "file_name_simple": self.data_file.file.name.split(".")[0],
            "global_clues": build_global_geo(self.global_clues),
            "global_delegation": build_global_geo(self.global_delegation),
            "global_transformations": global_transformations,
            "available_deliveries": build_available_deliveries(),
            "decode": self.file_control.decode,
            "hash_null": hash_null,
            "delimiter": self.delimiter,
            "row_start_data": self.file_control.row_start_data,
            "provider_id": self.provider.id,
            "split_by_delegation": self.provider.split_by_delegation,
            "columns_count": self.columns_count,
            "editable_models": self.editable_models,
            "real_models": self.real_models,
            "model_fields": self.model_fields,
            "existing_fields": self.existing_fields,
            "is_prepare": self.is_prepare,
            "lap": final_lap,
            "string_date": string_date,
        }
        if init_data["split_by_delegation"]:
            init_data["delegation_cat"] = build_catalog_delegation_by_id(
                self.institution, key_field="name")
        self.init_data = init_data

    def build_csv_converted(self, is_prepare=False):
        from respond.views import SampleFile

        self.is_prepare = is_prepare

        missing_criteria = self.calculate_minimals_criteria()
        string_date, date_error = self.get_date_format()
        if not string_date:
            missing_criteria.append(date_error)
        # elif string_date == "MANY":
        if self.lap > 0:
            missing_criteria.append("Ya se ha insertado este archivo")
        invalid_fields = self.name_columns.filter(
            final_field__included_code__in=["wait", "invalid"])
        for invalid_field in invalid_fields:
            ff = invalid_field.final_field
            name_in_data = get_name_in_data(invalid_field)
            missing_criteria.append(
                f"La columna '{name_in_data} --> {ff.verbose_name}' "
                f"aún no está lista para ser usado")
        if missing_criteria:
            print("missing_criteria", missing_criteria)
            error = f"No pasó la validación básica: " \
                f"{missing_criteria}"
            return [], [error], None

        # self.build_existing_fields()
        final_lap = -1 if self.is_prepare else self.lap
        self.build_init_data(final_lap, string_date)

        self.task_params["function_after"] = "build_csv_data_from_aws"

        sample_file = SampleFile()
        for sf in self.calculate_sheets():
            sheet_file = sf["sheet_file"]
            params = sf["params"]
            lap_sheet, created = LapSheet.objects.get_or_create(
                sheet_file=sheet_file, lap=final_lap)
            # init_data["lap_sheet_id"] = lap_sheet.id
            params["init_data"]["lap_sheet_id"] = lap_sheet.id
            self.task_params["models"] = [self.data_file, sheet_file]

            if is_prepare:
                try:
                    params["file"] = sample_file.get_file_path(sheet_file)
                except ValueError as e:
                    return [], [str(e)], self.data_file
                # init_data["sample_data"] = sheet_file.sample_data
            self.send_lambda("start_build_csv_data", params)
        return self.all_tasks, [], self.data_file

    def build_existing_fields(self):

        if self.existing_fields:
            return self.existing_fields

        simple_fields = [
            # Generales receta
            ["date_release"],
            ["date_visit"],
            ["date_delivery"],
            ["folio_document"],
            ["document_type"],
            ["prescribed_amount"],
            ["delivered_amount"],
            ["not_delivered_amount"],
            ["clasif_assortment"],
            ["clasif_assortment_presc"],
            ["price:Drug"],
        ]
        all_errors = []

        def build_column_data(name_col, final_name=None):

            data_type = name_col.final_field.data_type.name if \
                name_col.final_field.data_type else None
            new_column = {
                "name": final_name,
                "name_column": name_col.id,
                "name_in_data": name_col.name_in_data,
                "position": name_col.position_in_data,
                "required_row": name_col.required_row,
                "name_field": name_col.final_field.name,
                "public_name": name_col.final_field.verbose_name,
                "final_field_id": name_col.final_field.id,
                "collection": name_col.final_field.collection.model_name,
                "data_type": data_type,
                "regex_format": name_col.final_field.regex_format,
                "column_type": name_col.column_type.name,
                "parent": name_col.parent_column.id if name_col.parent_column else None,
                "child": name_col.child_column.id if name_col.child_column else None,
            }
            if name_col.final_field.collection.model_name == "Diagnosis":
                new_column["is_list"] = True
            is_special_column = name_col.column_type.name != "original_column"
            if is_special_column:
                new_column["is_special"] = True
            # if name_col.final_field.is_unique:
            #     new_column["is_unique"] = True

            valid_transformation = name_col.column_transformations.all() \
                .exclude(clean_function__ready_code="not_ready")
            # ready_codes = valid_transformation.values_list(
            #     "clean_function__ready_code", flat=True)
            # unique_codes = set(ready_codes)
            # if len(unique_codes) != len(ready_codes):
            #     name_in_data2 = get_name_in_data(column)
            #     clean_functions = valid_transformation.values_list(
            #         "clean_function__name", flat=True)
            #     err = f"La columna {name_in_data2} tiene más de una " \
            #           f"transformación especial que no se pueden aplicar a " \
            #           f"la vez: {clean_functions}"
            #     all_errors.append(err)
            if valid_transformation.exists():
                for transformation in valid_transformation:
                    clean_function = transformation.clean_function
                    ready_code = clean_function.ready_code
                    value = transformation.addl_params.get("value", True)
                    if ready_code == "need_value" and not isinstance(value, str):
                        all_errors.append(
                            f"La transformación {clean_function} "
                            f"necesita un valor, no puede estar vacía")
                    new_column[clean_function.name] = value
            return new_column

        included_columns = []
        for simple_field in simple_fields:
            field_name = simple_field[0].split(":")
            name_to_local = simple_field[1] \
                if len(simple_field) > 1 else field_name[0]
            query_fields = {"final_field__name": field_name[0]}
            if len(field_name) > 1:
                query_fields["final_field__collection__model_name"] = field_name[1]
            name_column = self.name_columns.filter(**query_fields).first()
            if name_column:
                included_columns.append(name_column.id)
                new_name_column = build_column_data(name_column, name_to_local)
                self.existing_fields.append(new_name_column)

        other_name_columns = self.name_columns.exclude(id__in=included_columns)
        for name_column in other_name_columns:
            if not name_column.final_field:
                name_in_data = get_name_in_data(name_column)
                all_errors.append(
                    f"La columna {name_in_data} no tiene campo final referido")
                continue
            final_field = name_column.final_field
            duplicated_in = None
            collection_name = final_field.collection.model_name
            snake_collection = camel_to_snake(collection_name)
            # snake_collection = final_field.collection.snake_name

            for prev_field in self.existing_fields:
                if prev_field.get("final_field_id") == final_field.id:
                    if snake_collection not in ["others", "diagnosis"]:
                        duplicated_in = prev_field
                        break
            name_to_local = f"{snake_collection}_{final_field.name}"
            new_name_column = build_column_data(name_column, name_to_local)
            if duplicated_in:
                new_name_column["duplicated_in"] = duplicated_in
            self.existing_fields.append(new_name_column)

        if not self.existing_fields:
            error = "No se encontraron campos para crear las recetas"
            all_errors.append(error)
        self.existing_fields = sorted(
            self.existing_fields, key=lambda x: x.get("position", 90) or 99)
        return self.existing_fields, all_errors

    def calculate_minimals_criteria(self):

        existing_fields, init_errors = self.build_existing_fields()

        def has_matching_dict(key, val):
            for dict_item in existing_fields:
                if dict_item[key] == val:
                    return True
            return False

        # has_delegation = bool(self.global_delegation)
        # if not has_delegation:
        #     has_delegation = has_matching_dict("collection", "Delegation")
        some_data_time = has_matching_dict("data_type", "Datetime")
        has_folio = has_matching_dict("name", "folio_document")
        some_amount = self.name_columns\
            .filter(final_field__name__contains="amount").exists()
        # key_medicine = has_matching_dict("name", "key2")
        some_medicine = has_matching_dict("collection", "Medicament")
        some_clues = has_matching_dict("collection", "MedicalUnit")
        if not some_clues:
            some_clues = bool(self.global_clues)
        # if not some_medicine:
        #     for field in existing_fields:
        #         if field["name"] == "name" and field["collection"] == "Container":
        #             some_medicine = True

        detailed_criteria = {
            # "Datos de delegación": has_delegation,
            "No tiene ninguna fecha": some_data_time,
            "No contiene Folio de receta": has_folio,
            "Falta alguna cantidad": some_amount,
            # "Clave de medicamento": key_medicine,
            "No tiene datos de medicamentos": some_medicine,
            "No tiene datos geográficos": some_clues,
        }
        missing_criteria = init_errors
        for criteria_name, value in detailed_criteria.items():
            if not value:
                missing_criteria.append(criteria_name)
        # if not key_medicine:
        #     if some_medicine:
        #         missing_criteria.append(
        #             "Hay campos de medicamento, pero aún no los procesamos")
        #     else:
        #         missing_criteria.append("Algún medicamentos")
        special_columns = self.name_columns.filter(
            column_type__clean_functions__isnull=False,
            column_transformations__isnull=True)
        for column in special_columns:
            error_text = f"La columna de tipo {column.column_type.public_name}" \
                f" no tiene la transformación que le corresponde"
            missing_criteria.append(error_text)

        control_invalid_transformations = self.file_control.file_transformations\
            .filter(clean_function__ready_code="not_ready")

        invalid_transformations = Transformation.objects.filter(
            name_column__file_control=self.file_control,
            clean_function__ready_code="not_ready")

        def add_transformation_error(transform):
            public_name = transform.clean_function.public_name
            error_txt = f"La transformación {public_name} aún no está soportada"
            missing_criteria.append(error_txt)

        for transformation in control_invalid_transformations:
            add_transformation_error(transformation)
        for transformation in invalid_transformations:
            add_transformation_error(transformation)
        return missing_criteria

    def get_date_format(self):
        from data_param.models import Transformation

        transformations = Transformation.objects.filter(
            clean_function__name="format_date",
            name_column__file_control=self.file_control)
        transformation_count = transformations.count()
        if transformation_count == 0:
            return None, "Ninguna de las columnas con fechas tiene su " \
                         "formato especificado"
        elif transformation_count > 1:
            date_fields = [field for field in self.existing_fields
                           if field["data_type"] == "Datetime"
                           and not field.get("almost_empty")]
            if len(date_fields) == transformation_count:
                return "MANY", None
            else:
                return None, "No todas las fechas tienen especificado su formato"
        first_value = transformations.first().addl_params.get("value")
        return first_value, None

    def save_catalog_csv(self, path, model_name):
        from scripts.common import get_file, start_session
        s3_client, dev_resource = start_session()
        complete_file = get_file(self, dev_resource)
        complete_file = complete_file.read()
