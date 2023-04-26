from data_param.models import Transformation
from scripts.common import start_session, create_file
import json
from task.serverless import camel_to_snake
from classify_task.models import Stage, StatusTask
from inai.models import DataFile, LapSheet


def sheet_name_to_file_name(sheet_name):
    import re
    valid_characters = re.sub(r'[\\/:*?"<>|]', '_', sheet_name)
    valid_characters = valid_characters.strip()
    valid_characters = re.sub(r'\s+', ' ', valid_characters)
    valid_characters = valid_characters.replace(' ', '_')

    return valid_characters


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
        })
    return all_models


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


class Match:

    def __init__(self, data_file: DataFile, task_params=None):
        from inai.models import set_upload_path
        from data_param.models import NameColumn
        from category.models import FileFormat
        self.data_file = data_file
        self.lap = self.data_file.next_lap
        petition = data_file.petition_file_control.petition
        self.file_control = data_file.petition_file_control.file_control
        self.agency = petition.agency
        entity = self.agency.entity
        self.institution = entity.institution
        self.global_clues = entity.ent_clues.first() if entity.is_clues else None
        # print("self.institution.code", self.institution.code)
        self.global_delegation = self.global_clues.delegation \
            if self.global_clues else None
        # print("global_delegation", self.global_delegation)
        only_name = f"NEW_ELEM_NAME_{self.data_file.id}_SHEET_NAME_lap{self.lap}.csv"
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

        s3_client, dev_resource = start_session()
        self.s3_client = s3_client

    def build_csv_converted(self, is_prepare=False):
        from scripts.common import build_s3
        from task.serverless import async_in_lambda
        import hashlib

        string_date = self.get_date_format()
        missing_criteria = self.calculate_minimals_criteria()
        if not string_date:
            missing_criteria.append("Sin formato de fecha")
        if self.lap > 0:
            missing_criteria.append("Ya se ha insertado este archivo")
        invalid_fields = self.name_columns.filter(
            final_field__included_code__in=["wait", "invalid"])
        for invalid_field in invalid_fields:
            ff = invalid_field.final_field
            missing_criteria.append(
                f"El campo '{invalid_field.name_in_data} --> {ff.verbose_name}' "
                f"aún no está listo para ser usado")
        if missing_criteria:
            print("missing_criteria", missing_criteria)
            error = f"No pasó la validación básica: " \
                f"{missing_criteria}"
            return [], [error], self.data_file

        # self.build_existing_fields()

        value_null = "".encode(self.file_control.decode or "utf-8")
        hash_null = hashlib.md5(value_null).hexdigest()

        def build_global_geo(global_obj):
            if not global_obj:
                return None
            is_clues = global_obj.__class__.__name__ == "CLUES"
            final_dict = {"id": global_obj.id}
            if is_clues:
                is_tuple = isinstance(global_obj.clues, tuple)
                final_dict["clues_key"] = global_obj.clues
            else:
                final_dict["name"] = global_obj.name,
            return final_dict

        final_lap = -1 if is_prepare else self.lap
        init_data = {
            "file_name_simple": self.data_file.file.name.split(".")[0],
            "global_clues": build_global_geo(self.global_clues),
            "global_delegation": build_global_geo(self.global_delegation),
            "decode": self.file_control.decode,
            "hash_null": hash_null,
            "delimiter": self.delimiter,
            "row_start_data": self.file_control.row_start_data,
            "entity_id": self.agency.entity_id,
            "columns_count": self.columns_count,
            "editable_models": self.editable_models,
            "real_models": self.real_models,
            "model_fields": self.model_fields,
            "existing_fields": self.existing_fields,
            "is_prepare": is_prepare,
            "lap": final_lap,
            "string_date": string_date,
        }
        self.task_params["function_after"] = "build_csv_data_from_aws"
        all_tasks = []

        filter_sheets = self.data_file.filtered_sheets
        procesable_sheets = self.data_file.sheet_files.filter(
            matched=True, sheet_name__in=filter_sheets)
        transform_stage = Stage.objects.get(name="transform")
        finish_status = StatusTask.objects.get(name="finished")
        remaining_prev_stage = procesable_sheets.filter(
            stage__order__lt=transform_stage.order)
        remaining_same_stage = procesable_sheets.filter(
            stage=transform_stage, status__order__lt=finish_status.order)
        remaining_sheets = remaining_prev_stage | remaining_same_stage
        if remaining_sheets.exists():
            sheets_to_process = remaining_sheets
        else:
            sheets_to_process = procesable_sheets
        # test_count = 0
        for sheet_file in sheets_to_process:
            lap_sheet, created = LapSheet.objects.get_or_create(
                sheet_file=sheet_file, lap=final_lap)

            init_data["sheet_name"] = sheet_file.sheet_name
            init_data["sheet_file_id"] = sheet_file.id
            init_data["lap_sheet_id"] = lap_sheet.id
            sheet_name2 = sheet_name_to_file_name(sheet_file.sheet_name)
            init_data["final_path"] = self.final_path.replace(
                "SHEET_NAME", sheet_name2)
            self.task_params["models"] = [self.data_file, sheet_file]
            params = {
                "init_data": init_data,
                "s3": build_s3(),
                "file": sheet_file.file.name,
            }
            if is_prepare:
                dump_sample = json.dumps(sheet_file.sample_data)
                final_path = f"catalogs/{self.agency.acronym}" \
                             f"/sample_file_{self.data_file.id}.json"
                file_sample, errors = create_file(
                    dump_sample, self.s3_client, final_path=final_path)
                if errors:
                    return [], errors, self.data_file
                params["file"] = file_sample
                # init_data["sample_data"] = sheet_file.sample_data
            async_task = async_in_lambda(
                "start_build_csv_data", params, self.task_params)
            if async_task:
                all_tasks.append(async_task)
            # # RICK 22: Pruebas
            # test_count += 1
            # if test_count > 2:
            #     break
        return all_tasks, [], self.data_file

    def build_existing_fields(self):

        if self.existing_fields:
            return self.existing_fields

        simple_fields = [
            # Generales receta
            ["date_release"],
            ["date_delivery"],
            ["date_visit"],
            ["folio_document"],
            ["document_type"],
            ["prescribed_amount"],
            ["delivered_amount"],
            ["clasif_assortment_presc"],
            ["price:Drug"],
        ]
        all_errors = []

        def build_column_data(column, final_name=None):
            is_special_column = column.column_type.name != "original_column"
            new_column = {
                "name": final_name,
                "name_column": column.id,
                "name_in_data": column.name_in_data,
                "position": column.position_in_data,
                "required_row": column.required_row,
                "name_field": column.final_field.name,
                "final_field_id": column.final_field.id,
                "collection": column.final_field.collection.model_name,
                "is_unique": column.final_field.is_unique,
                "data_type": column.final_field.data_type.name if \
                             column.final_field.data_type else None,
                "regex_format": column.final_field.regex_format,
                "is_special": is_special_column,
                "column_type": column.column_type.name,
                "parent": column.parent_column.id if column.parent_column else None,
                "child": column.child_column.id if column.child_column else None,
            }
            # if is_special_column:
            special_functions = [
                "fragmented", "concatenated", "only_params_parent",
                "only_params_child", "text_nulls"]
            transformation = column.column_transformations \
                .filter(clean_function__name__in=special_functions)
            if transformation.count() > 1:
                error = f"La columna {column.name_in_data} tiene más de una " \
                        f"función especial que no se pueden aplicar a la vez"
                all_errors.append(error)
            elif transformation.exist():
                first_t = transformation.first()
                new_column["clean_function"] = first_t.clean_function.name
                new_column["t_value"] = first_t.addl_params.get("value")
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

        other_name_columns = self.name_columns\
            .exclude(id__in=included_columns)
        for name_column in other_name_columns:
            if not name_column.final_field:
                error = f"La columna {name_column.name_in_data} no tiene " \
                        f"campo final referido"
                all_errors.append(error)
                continue
            final_field = name_column.final_field
            duplicated_in = None
            for prev_field in self.existing_fields:
                if prev_field.get("final_field_id") == final_field.id:
                    duplicated_in = prev_field
                    break
            collection_name = final_field.collection.model_name
            collection_name = camel_to_snake(collection_name)
            name_to_local = f"{collection_name}_{final_field.name}"
            new_name_column = build_column_data(name_column, name_to_local)
            self.existing_fields.append(new_name_column)
            if duplicated_in:
                self.existing_fields[-1]["duplicated_in"] = duplicated_in

        if not self.existing_fields:
            error = "No se encontraron campos para crear las recetas"
            all_errors.append(error)
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
            transformation = column.column_transformations.first()
            error_text = f"La columna de tipo {column.column_type.public_name}" \
                f" no tiene la transformación {transformation.clean_function.public_name}"
            missing_criteria.append(error_text)
        valid_control_trans = [
            "include_tabs_by_name", "exclude_tabs_by_name",
            "include_tabs_by_index", "exclude_tabs_by_index",
            "only_cols_with_headers", "no_valid_row_data"]
        control_transformations = self.file_control.file_transformations\
            .exclude(clean_function__name__in=valid_control_trans)
        valid_column_trans = [
            "fragmented", "concatenated", "format_date", "clean_key_container",
            "get_ceil", "only_params_parent", "only_params_child",
            "global_variable", "text_nulls", "almost_empty"]
        related_transformations = Transformation.objects\
            .filter(name_column__file_control=self.file_control)\
            .exclude(clean_function__name__in=valid_column_trans)
        # column_transformations = self.name_columns.column_transformations\
        #     .exclude(clean_function__name__in=valid_column_trans)

        def add_transformation_error(transform):
            public_name = transform.clean_function.public_name
            error_txt = f"La transformación {public_name} aún no está soportada"
            missing_criteria.append(error_txt)

        for transformation in control_transformations:
            add_transformation_error(transformation)
        for transformation in related_transformations:
            add_transformation_error(transformation)
        return missing_criteria

    def get_date_format(self):
        from data_param.models import Transformation
        transformation = Transformation.objects.filter(
            clean_function__name="format_date",
            file_control=self.file_control).first()
        if not transformation:
            transformation = Transformation.objects.filter(
                clean_function__name="format_date",
                name_column__file_control=self.file_control).first()
        return transformation.addl_params.get("value") \
            if transformation else None  # '%Y-%m-%d %H:%M:%S.%fYYY'

    def save_catalog_csv(self, path, model_name):
        from task.serverless import async_in_lambda
        from scripts.common import get_file, start_session
        s3_client, dev_resource = start_session()
        complete_file = get_file(self, dev_resource)
        complete_file = complete_file.read()
