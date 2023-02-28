import io


import unidecode

import csv
import uuid as uuid_lib
from catalog.models import Delegation, CLUES, State
from inai.models import NameColumn, DataFile
from formula.models import (MissingRow, MissingField, Prescription, Drug)
catalog_state = {}
raws = {}
delegation_value_list = [
    'name', 'other_names', 'state__short_name', 'id', 'clues']

from django.conf import settings


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter


def calculate_delivered(available_data):
    prescribed_amount = available_data.get("prescribed_amount")
    if not prescribed_amount:
        error = "No se pudo determinar si se entregó o no"
        return None, error

    delivered = "unknown"

    delivered_amount = available_data.get("delivered_amount")
    not_delivered_amount = available_data.pop("not_delivered_amount", None)
    if not_delivered_amount is not None and delivered_amount is None:
        delivered_amount = prescribed_amount - not_delivered_amount
        available_data["delivered_amount"] = delivered_amount

    if prescribed_amount and delivered_amount is not None:
        if prescribed_amount == delivered_amount:
            delivered = "complete"
        elif prescribed_amount > delivered_amount:
            delivered = "partial"
        elif not delivered_amount:
            delivered = "denied"
    else:
        error = "No se pudo determinar si se entregó o no"
        return None, error
    available_data["delivered"] = delivered
    return available_data, None


def calculate_delivered_final(all_delivered):
    some_unknown = [d for d in all_delivered if d == "unknown"]
    if some_unknown:
        return "unknown"
    partials = [d for d in all_delivered if d == "partial"]
    if partials:
        return "partial"
    completes = [d for d in all_delivered if d == "complete"]
    if len(all_delivered) == len(completes):
        return "complete"
    only_denied = [d for d in all_delivered if d == "denied"]
    if len(all_delivered) == len(only_denied):
        return "denied"
    return "partial"


def field_of_models(model_name):
    from django.apps import apps
    my_model = apps.get_model('formula', model_name)
    all_fields = my_model._meta.get_fields(
        include_parents=False, include_hidden=False)
    return [field.name for field in all_fields
            if not field.one_to_many]


class Match:

    def __init__(self, data_file: DataFile, task_params=None):

        self.sample_size = 20

        self.data_file = data_file
        self.data_file_id = data_file.id
        # self.build_csv_converted()
        petition = data_file.petition_file_control.petition
        file_control = data_file.petition_file_control.file_control
        self.file_control_id = file_control.id
        self.decode = file_control.decode
        self.row_start_data = file_control.row_start_data

        self.entity = petition.entity
        self.institution = self.entity.institution
        global_state = self.entity.state
        global_clues = self.entity.clues
        self.global_clues_id = global_clues.id if global_clues else None
        global_delegation = None
        if self.institution.code == "INSABI":
            if global_state:
                delegation_name = f"{global_state.short_name} - INSABI"
                global_delegation = Delegation.objects.filter(
                    name=delegation_name).first()
        elif global_clues:
            global_delegation = global_clues.related_delegation
        self.global_delegation_id = global_delegation.id \
            if global_delegation else None
        self.global_state_id = global_state.id if global_state else None

        self.name_columns = NameColumn.objects \
            .filter(file_control=file_control) \
            .prefetch_related(
                "final_field",
                "final_field__collection",
                "final_field__parameter_group",
            )

        original_columns = self.name_columns.filter(
            position_in_data__isnull=False)
        self.delimiter = file_control.delimiter or ','
        self.columns_count = original_columns.count()

        self.final_lists = [
            {"name": "drug", "model": "Drug"},
            {"name": "prescription", "model": "Prescription"},
            {"name": "row", "model": "MissingRow"},
            {"name": "field", "model": "MissingField"},
        ]
        self.model_fields = {curr_list["name"]: field_of_models(curr_list["model"])
                             for curr_list in self.final_lists}
        print("self.model_fields", self.model_fields)

        self.last_missing_row = None

        self.all_missing_rows = []
        self.all_missing_fields = []
        self.catalog_clues = {}
        self.catalog_clues_by_id = {}
        self.catalog_state = {}
        self.catalog_delegation = {}
        self.catalog_container = {}
        self.claves_medico_dict = {}
        self.existing_fields = []

    def build_csv_converted(self):
        from datetime import datetime

        from scripts.common import get_file, start_session

        # print("prescription_fields", prescription_fields, "\n\n")
        self.build_catalogs()
        self.build_catalog_container()

        self.build_existing_fields()
        has_minimals_criteria, detailed_criteria = \
            self.calculate_minimals_criteria()
        if not has_minimals_criteria:
            print("detailed_criteria", detailed_criteria)
            error = {"text": "No se encontraron todas las columnas esenciales",
                      "detailed_criteria": detailed_criteria}
            return [], [error], None

        string_date = self.get_date_format()
        # print("string_date", string_date)
        unique_clues = {}
        for existing_field in self.existing_fields:
            if existing_field["collection"] == "CLUES" and \
                    existing_field["is_unique"]:
                unique_clues = existing_field
                break

        # last_date = None
        # iso_date = None
        # first_iso = None

        all_prescriptions = {}
        # all_prescription_data = []
        # provisional_list = []
        # provisional_drug_list = []
        # all_drug_data = []

        # data_rows = data_rows[self.file_control.row_start_data:]
        s3_client, dev_resource = start_session()
        complete_file = get_file(self.data_file, dev_resource)
        data_rows = complete_file.readlines()

        all_data = self.divide_rows(data_rows)
        # for seq, row in enumerate(data_rows, start=self.file_control.row_start_data):
        csv_buffer = {}
        csv_files = {}
        for elem in self.final_lists:
            csv_files[elem["name"]] = io.StringIO()
            csv_buffer[elem["name"]] = csv.writer(
                csv_files[elem["name"]], delimiter=self.delimiter)

        for row in all_data:
            # print("data_row \t", data_row)
            self.last_missing_row = None
            # is_same_date = False
            available_data = {
                "data_file": self.data_file_id,
                "row_seq": row[0],
                "uuid": uuid_lib.uuid4()
            }
            available_data, some_date = self.complement_available_data(
                available_data, row, string_date)

            if not some_date:
                error = "No se pudo convertir ninguna fecha"
                self.all_missing_rows[-1][-1] = error
                continue
            # if last_date != date[:10]:
            #     last_date = date[:10]
            iso_date = some_date.isocalendar()
            available_data["iso_year"] = iso_date[0]
            available_data["iso_week"] = iso_date[1]
            available_data["iso_day"] = iso_date[2]
            available_data["month"] = some_date.month
            # if not first_iso:
            #     first_iso = iso_date

            available_data, error = calculate_delivered(available_data)
            if error:
                self.append_missing_row(row[0], row[1:], error)
                continue
            delivered = available_data.get("delivered")

            available_data = self.medicine_match(available_data)

            folio_document = available_data.get("folio_document")
            folio_ocamis = "%s-%s-%s-%s" % (
                self.entity.id, iso_date[0], iso_date[1], folio_document)

            curr_prescription = all_prescriptions.get(folio_ocamis)
            if curr_prescription:
                available_data["prescription"] = curr_prescription["uuid_folio"]
                all_delivered = curr_prescription["all_delivered"]
                all_delivered += [delivered]
                curr_prescription["all_delivered"] = all_delivered
                curr_prescription["delivered_final"] = calculate_delivered_final(
                    all_delivered)
            else:
                uuid_folio = uuid_lib.uuid4()
                available_data["uuid_folio"] = uuid_folio
                available_data["prescription"] = uuid_folio
                available_data["delivered_final"] = delivered
                available_data["folio_ocamis"] = folio_ocamis
                available_data["folio_document"] = folio_document
                available_data["all_delivered"] = [delivered]

                clues = self.clues_match(available_data, unique_clues)
                available_data["clues"] = clues
                delegation, delegation_error = self.delegation_match(
                    available_data, clues)
                if not delegation:
                    self.append_missing_row(row[0], row[1:], delegation_error)
                    continue
                available_data["delegation"] = delegation

                all_prescriptions[folio_ocamis] = available_data

            current_drug_data = []
            # current_provisional_drug_data = {}
            for drug_field in self.model_fields["drug"]:
                value = available_data.pop(drug_field, None)
                if not value:
                    value = locals().get(drug_field)
                # value = available_data.get(drug_field, locals().get(drug_field))

                current_drug_data.append(value)
                # current_provisional_drug_data[drug_field] = value
            csv_buffer["drug"].writerow(current_drug_data)
            # all_drug_data.append(current_drug_data)
            # provisional_drug_list.append(current_provisional_drug_data)

            # IMPORTANTE: Falta un proceso para los siguientes campos:
            # doctor = None
            # area = None
            # diagnosis = None

            if len(all_prescriptions) > self.sample_size:
                break

        for curr_prescription in all_prescriptions.values():
            current_prescription_data = []
            # current_provisional_data = {}
            # curr_prescription = all_prescriptions.get(folio)
            for field_name in self.model_fields["prescription"]:
                value = curr_prescription.get(field_name, locals().get(field_name))
                current_prescription_data.append(value)
                # current_provisional_data[field_name] = value
            # all_prescription_data.append(current_prescription_data)
            csv_buffer["prescription"].writerow(current_prescription_data)
            # provisional_list.append(current_provisional_data)

        self.save_list_in_s3(self.all_missing_rows, "row")
        # csv_buffer_row = csv.writer(io.StringIO())
        # csv_buffer_row.writerows(self.all_missing_rows)
        # body = csv_buffer_row.getvalue()


        # csv_buffer["field"].writerows(self.all_missing_fields)
        s3_client, dev_resource = start_session()
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_location = getattr(settings, "AWS_LOCATION")
        from inai.models import set_upload_path
        all_final_paths = []

        for elem_list in self.final_lists:
            only_name = f"{elem_list['name']}_{self.data_file_id}.csv"
            final_path = set_upload_path(self.data_file, only_name)
            all_final_paths.append({
                "name": elem_list["name"],
                "path": final_path,
            })
            print(final_path)
            s3_client.put_object(
                Body=csv_files[elem_list["name"]].getvalue(),
                Bucket=bucket_name,
                Key=f"{aws_location}/{final_path}",
                ContentType="text/csv",
                ACL="public-read",
            )
            self.send_csv_to_db(final_path, elem_list)
        return [], [], all_final_paths

    def build_existing_fields(self):

        if self.existing_fields:
            return self.existing_fields

        simple_fields = [
            ["date_release"],
            ["date_visit"],
            ["date_delivery"],
            ["folio_document"],
            ["name:DocumentType", "document_type"],
            ["prescribed_amount"],
            ["delivered_amount"],
            ["budget_key"],
            ["key2:Container", "key2"],
            ["rn"],
            ["price:Drug", "price"],
            ["folio_document"],
            ["name:Delegation", "delegation_name"],
            ["clues:CLUES", "clave_clues"],
            ["key_issste:CLUES", "key_issste"],
            ["id_clues:CLUES", "id_clues"],
        ]

        for simple_field in simple_fields:
            field_name = simple_field[0].split(":")
            name_to_local = simple_field[1] \
                if len(simple_field) > 1 else field_name[0]
            query_fields = {"final_field__name": field_name[0]}
            if len(field_name) > 1:
                query_fields["final_field__collection__model_name"] = field_name[1]
            column = self.name_columns.filter(**query_fields).first()
            if column:
                self.existing_fields.append({
                    "name": name_to_local,
                    "name_column": column.id,
                    "position": column.position_in_data,
                    "collection": column.final_field.collection.model_name,
                    "is_unique": column.final_field.is_unique,
                    "data_type": column.final_field.data_type.name,
                })
        if not self.existing_fields:
            raise Exception("No se encontraron campos para crear las recetas")
        return self.existing_fields

    def calculate_minimals_criteria(self):

        existing_fields = self.build_existing_fields()

        def has_matching_dict(key, value):
            for dict_item in existing_fields:
                if dict_item[key] == value:
                    return True
            return False

        has_delegation = bool(self.global_delegation_id)
        if not has_delegation:
            has_delegation = has_matching_dict("collection", "Delegation")
        some_data_time = has_matching_dict("data_type", "Datetime")
        has_folio = has_matching_dict("name", "folio_document")
        some_amount = self.name_columns\
            .filter(final_field__name__contains="amount").exists()
        some_medicine = has_matching_dict("name", "key2") or \
            has_matching_dict("name", "_own_key")
        if not some_medicine:
            for field in existing_fields:
                if field["name"] == "name" and field["collection"] == "Container":
                    some_medicine = True

        detailed_criteria = {
            "has_delegation": has_delegation,
            "some_data_time": some_data_time,
            "has_folio": has_folio,
            "some_amount": some_amount,
            "some_medicine": some_medicine,
        }
        every_criteria = True
        for value in detailed_criteria.values():
            if not value:
                every_criteria = False
                break
        return every_criteria, detailed_criteria

    def divide_rows(self, data_rows):

        structured_data = []
        sample = data_rows[:20]
        decode = self.obtain_decode(sample)

        if decode == "unknown":
            error = "No se pudo decodificar el archivo"
            return [], [error], None

        begin = self.row_start_data

        for row_seq, row in enumerate(data_rows[begin:self.sample_size], start=begin):
            # print("Row: %s" % row_seq)
            self.last_missing_row = None
            row_decode = row.decode(decode) if decode != "str" else str(row)
            # .replace('\r\n', '')
            row_data = row_decode.replace('\r\n', '').split(self.delimiter)
            if len(row_data) == self.columns_count:
                row_data.insert(0, str(row_seq))
                structured_data.append(row_data)
            else:
                errors = ["Conteo distinto de Columnas: %s de %s" % (
                    len(row_data), self.columns_count)]
                self.append_missing_row(row_seq, row, errors)

        return structured_data

    def complement_available_data(self, available_data, row, string_date):
        from datetime import datetime
        some_date = None
        for field in self.existing_fields:
            # RICK 16 Convertir esto en una función aparte
            value = row[field["position"]]
            if field["data_type"] == "Datetime":  # and not is_same_date:
                # if value == last_date:
                #     is_same_date = True
                try:
                    value = datetime.strptime(value, string_date)
                    if not some_date:
                        some_date = value
                        # last_date = value
                except ValueError:
                    error = "No se pudo convertir la fecha"
                    self.append_missing_field(
                        row, field["column"], row[0], value, error)
                    value = None
            elif field["data_type"] == "Integer":
                try:
                    value = int(value)
                except ValueError:
                    error = "No se pudo convertir a número entero"
                    self.append_missing_field(
                        row, field["column"], row[0], value, error)
                    value = None
            elif field["data_type"] == "Float":
                try:
                    value = float(value)
                except ValueError:
                    error = "No se pudo convertir a número decimal"
                    self.append_missing_field(
                        row, field["column"], row[0], value, error)
                    value = None
            available_data[field["name"]] = value
        return available_data, some_date

    def medicine_match(self, available_data):
        if available_data.get("key2"):
            new_key2 = available_data["key2"].replace(".", "")
            available_data["key2"] = new_key2
            curr_container = self.catalog_container.get(new_key2)
            available_data["container"] = curr_container
        return available_data

    def clues_match(self, available_data, unique_clues):
        clues = None
        clave_clues = available_data.pop(unique_clues.get("name"), None)
        if self.global_clues_id:
            clues = self.global_clues_id
        elif clave_clues and self.catalog_clues_by_id:
            try:
                clues = self.catalog_clues_by_id.get(clave_clues)
            except KeyError:
                pass
        return clues

    def create_delegation(self, delegation_name, clues_id):
        print("ME MANDO A DELEGATION CREATE")
        if self.institution.code in ["ISSSTE", "IMSS"]:
            try:
                clues_obj = CLUES.objects.get(id=clues_id)
                del_obj, created = Delegation.objects.get_or_create(
                    institution=self.institution,
                    name=delegation_name,
                    clues=clues_obj,
                    state=clues_obj.state,
                )
                delegation = del_obj.id
                final_delegation = {}
                for field in delegation_value_list:
                    final_delegation[field] = getattr(del_obj, field)
                self.catalog_delegation[delegation_name] = final_delegation
                return delegation, None
            except Exception as e:
                return None, "No se pudo crear la delegación, ERROR: %s" % e
        else:
            error = "Por alguna razón, no es ISSSTE o IMSS y no tiene delegación"
            return None, error

    def obtain_decode(self, sample):
        if self.decode:
            return self.decode

        for row in sample:
            is_byte = isinstance(row, bytes)
            # print("type: %s" % type(row))
            # print("is_byte: %s" % isinstance(row, bytes))
            # print("row: %s" % row)
            # print("++++++++++++++++++++")
            posible_latin = False
            if is_byte:
                try:
                    row.decode("utf-8")
                except:
                    posible_latin = True
                if posible_latin:
                    try:
                        row.decode("latin-1")
                        return "latin-1"
                    except Exception as e:
                        print(e)
                        return "unknown"
            else:
                return "str"
        return "utf-8"

    def append_missing_row(self, row_seq, original_data, error=None):
        if self.last_missing_row:
            self.all_missing_rows[-1][-1] = error
            return self.all_missing_rows[-1][0]
        missing_data = []
        uuid = str(uuid_lib.uuid4())
        data_file = self.data_file_id
        for field_name in self.model_fields["row"]:
            value = locals().get(field_name)
            missing_data.append(value)
        self.last_missing_row = missing_data
        self.all_missing_rows.append(missing_data)
        return uuid

    def append_missing_field(
            self, row, name_column, row_seq, original_value, error):
        missing_row = self.append_missing_row(row_seq, row)
        missing_field = []
        uuid = str(uuid_lib.uuid4())
        #if name_column:
        #    name_column = name_column.id
        print("error: %s" % error)
        for field_name in self.model_fields["field"]:
            value = locals().get(field_name)
            missing_field.append(value)
        self.all_missing_fields.append(missing_field)

    def build_catalogs(self):
        from inai.models import NameColumn
        from data_param.models import FinalField

        # Se obtienen las variables que forman parte del data_file actual:
        # current_fields = FinalField.objects.filter(
        #     name_column__file_control__petition_file_control__data_file=self)
        # recipe_fields = current_fields.filter(
        #     collection__model_name='Prescription').values()
        # drug_fields = current_fields.filter(
        #     collection__model_name='Drug').values()
        columns = {"all": self.name_columns.values()}
        clues_unique = self.name_columns.filter(
            final_field__collection__model_name='CLUES',
            final_field__is_unique=True).first()
        if clues_unique:
            self.build_catalog_clues_by_id(clues_unique.final_field.name)
        columns["delegation"] = self.name_columns.filter(
            final_field__collection__model_name='Delegation').values()
        if not self.global_delegation_id and columns["delegation"]:
            self.build_catalog_delegation()

        if None:
            columns["clues"] = self.name_columns.filter(
                final_field__parameter_group__name='CLUES y Geográfico').values()
            columns["state"] = self.name_columns.filter(
                final_field__collection__model_name='State').values()
            if not self.global_state_id and columns["state"]:
                self.build_catalog_state()
            if columns["clues"]:
                self.build_catalog_clues()
        # for collection, collection_name in collections.items():
        #     columns[collection] = self.name_columns.filter(
        #         final_field__collection=collection_name).values('name')

    def build_catalog_delegation(self):
        from catalog.models import Delegation

        curr_delegations = Delegation.objects.filter(institution=self.institution)
        if self.global_state_id:
            curr_delegations = curr_delegations.filter(state_id=self.global_state_id)
        # delegation_value_list = ['name', 'other_names', 'state__short_name', 'id']
        delegations_query = list(curr_delegations.values(*delegation_value_list))
        for delegation in delegations_query:
            try:
                delegation_name = unidecode.unidecode(delegation["name"]).upper()
            except Exception:
                delegation_name = delegation["name"].upper()
            if delegation_name not in self.catalog_delegation:
                self.catalog_delegation[delegation_name] = delegation
            alt_names = delegation["other_names"] or []
            for alt_name in alt_names:
                if alt_name not in self.catalog_delegation:
                    self.catalog_delegation[alt_name] = delegation
                # else:
                #     self.catalog_delegation[alt_name].append(delegation)
        # print("DELEGATIONS: \n", self.catalog_delegation)
        # print("\n")

    def build_catalog_state(self):
        from catalog.models import State
        curr_states = State.objects.all()
        states_query = list(curr_states.values_list('name', 'short_name'))
        for estado in states_query:
            try:
                state_name = unidecode.unidecode(estado[0]).upper()
            except Exception:
                state_name = estado[0].upper()
            if state_name not in catalog_state:
                catalog_state[state_name] = [estado]
            try:
                state_short_name = unidecode.unidecode(estado[1]).upper()
            except Exception:
                state_short_name = estado[1].upper()
            if state_short_name not in catalog_state:
                catalog_state[state_short_name] = [estado]

    def build_catalog_clues_by_id(self, key_field):
        clues_data_query = CLUES.objects.filter(institution=self.institution)
        if self.global_state_id:
            clues_data_query.filter(state_id=self.global_state_id)
        value_list = ["id", key_field]
        clues_data_list = list(clues_data_query.values(*value_list))
        for clues_data in clues_data_list:
            clues_key = clues_data[key_field]
            self.catalog_clues_by_id[clues_key] = clues_data["id"]

    def build_catalog_clues(self):
        # RICK 16: adaptar a CLAVE CLUES POR LO PRONTO, también key_issste
        from catalog.models import CLUES

        clues_data_query = CLUES.objects.filter(institution=self.institution)
        if self.global_state_id:
            clues_data_query.filter(state_id=self.global_state_id)
        clues_data_query = list(
            clues_data_query.values_list(
                "state__name", "name", "typology_cve",
                "id", "alternative_names", "state__short_name"
            )
        )
        for clues_data in clues_data_query:
            cves = clues_data[2].split("/")
            state_short_name = clues_data[5]
            for cve in cves:
                try:
                    clues_name = unidecode.unidecode(clues_data[1])
                except Exception as e:
                    clues_name = clues_data[1]
                prov_name = "%s %s" % (cve, clues_name)
                real_name = unidecode.unidecode(prov_name).upper()
                if not self.global_state_id:
                    real_name = "%s$%s" % (real_name, state_short_name)
                if real_name not in self.catalog_clues:
                    self.catalog_clues[real_name] = [clues_data]
                else:
                    self.catalog_clues[real_name].append(clues_data)
            if clues_data[4]:
                for alt_name in clues_data[4]:
                    if not self.global_state_id:
                        alt_name = "%s$%s" % (alt_name, state_short_name)
                    if alt_name not in self.catalog_clues:
                        self.catalog_clues[alt_name] = [clues_data]
                    else:
                        self.catalog_clues[alt_name].append(clues_data)

    def build_catalog_container(self):
        from medicine.models import Container
        all_containers = Container.objects.all()
        containers_query = list(all_containers.values('key2', 'id'))
        for container in containers_query:
            self.catalog_container[container["key2"]] = container["id"]

    def state_match(self, row, columns, collection):
        return row

    def delegation_match(self, available_data, clues):
        delegation_name = available_data.pop("delegation_name", None)
        delegation = None
        if self.global_delegation_id:
            delegation = self.global_delegation_id
        elif delegation_name:
            delegation_error = None
            delegation_name = delegation_name.strip().upper()
            try:
                delegation_cat = self.catalog_delegation[delegation_name]
                delegation = delegation_cat["id"]
            except Exception as e:
                delegation_error = f"No se encontró la delegación" \
                                   f" {delegation_name} ({e})"
            if not delegation and clues:
                delegation, delegation_error = self.create_delegation(
                    delegation_name, clues)
        return delegation, delegation_error

    def execute_matches(self, row, file):
        # from formula.models import MissingRow
        missing_row = None
        if not self.global_state_id:
            columns_state = self.name_columns.filter(final_field__collection='State')
            if columns_state.exists():
                state = self.state_match(row, columns_state, 'State')
        # Delegación
        # columns_deleg = self.name_columns.filter(final_field__collection='Delegation')
        # if columns_deleg.exists():
        #     global_delegation = self.delegation_match(row, columns_state, 'Delegation')
        #     if not global_delegation:
        #         missing_row = MissingRow.objects.get_or_create(file=file)
        #         missing_row = MissingRow.objects.create(
        #             file=file, row_seq=row[0], orinal_data=row)
        #         pass
        #     if global_delegation and not self.global_state:
        #         self.global_state = global_delegation.state
        # recipe_row = []
        # if not self.global_state:
        #     pass

    def get_date_format(self):
        from inai.models import Transformation
        transformation = Transformation.objects.filter(
            clean_function__name="format_date",
            file_control_id=self.file_control_id).first()
        return transformation.addl_params["value"] \
            if transformation else '%Y-%m-%d %H:%M:%S.%f'

    def save_list_in_s3(self, list_to_save, list_name):
        return 2

    def send_csv_to_db(self, path, elem_list):
        import psycopg2

        model_name = elem_list["name"]
        columns = self.model_fields[model_name]
        columns_join = ",".join(columns)
        options = "csv DELIMITER ',' NULL 'NULL' ENCODING 'LATIN1'"
        model_in_db = f"formula_{model_name.lower()}"
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        region_name = getattr(settings, "AWS_S3_REGION_NAME")
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
        # '(format csv, header true)',
        # 'data_files/example.csv',
        # OPIONAL_SESSION_TOKEN = 'fFq7NwQyj/FmdtK/weXRwgrlEArkOatITD/mJYzL'
        sql_query_aws = f"""
            SELECT aws_s3.table_import_from_s3(
                '{model_in_db}',
                '{columns_join}',
                '(format csv, header false)',
                '{bucket_name}',
                '{path}',
                '{region_name}',
                '{access_key}'
            )
        """
        sql_query = f"""
            COPY {model_in_db} ({columns_join})
            FROM '{path}'
            {options}
        """
        # desabasto_db = settings.get("DATABASES", {}).get("default")
        desabasto_db = getattr(settings, "DATABASES", {}).get("default")
        connection = psycopg2.connect(
            database=desabasto_db.get("NAME"),
            user=desabasto_db.get("USER"),
            password=desabasto_db.get("PASSWORD"),
            host=desabasto_db.get("HOST"),
            port=desabasto_db.get("PORT"))
        cursor = connection.cursor()
        cursor.execute(sql_query)
        connection.commit()
        cursor.close()
        connection.close()
