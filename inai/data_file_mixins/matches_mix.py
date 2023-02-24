
import unidecode
catalog_state = {}
catalog_delegation = {}
raws = {}
state = None
institution = None
petition = None


def build_catalog_delegation():
    from catalog.models import Delegation
    global catalog_delegation
    #RICK Evaluar si es necesario declarar global acá:
    global state
    global institution
    curr_delegations = Delegation.objects.filter(institution=institution)
    if state:
        curr_delegations = curr_delegations.filter(state=state)
    delegations_query = list(curr_delegations.values_list(
        'name', 'other_names', 'state__short_name', 'id'))
    for deleg in delegations_query:
        try:
            delegation_name = unidecode.unidecode(deleg[0]).upper()
        except Exception:
            delegation_name = deleg[0].upper()
        if delegation_name not in catalog_delegation:
            catalog_delegation[delegation_name] = [deleg]
        alt_names = deleg[1] or []
        for alt_name in alt_names:
            if alt_name not in catalog_delegation:
                catalog_delegation[alt_name] = [deleg]
            else:
                catalog_delegation[alt_name].append(deleg)


def build_catalog_state():
    from catalog.models import State
    global catalog_state
    global catalog_delegation
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


#Función que se modificará con el trabajo de Itza:
def build_catalog_clues():
    from catalog.models import CLUES
    global catalog_clues
    #RICK Evaluar si es necesario declarar global acá:
    # global institution
    # global state
    clues_data_query = CLUES.objects.filter(institution=institution)
    if state:
        clues_data_query.filter(state=state)
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
            except Exception:
                clues_name = clues_data[1]
            prov_name = "%s %s" % (cve, clues_name)
            real_name = unidecode.unidecode(prov_name).upper()
            if not state:
                real_name = "%s$%s" % (real_name, state_short_name)
            if real_name not in catalog_clues:
                catalog_clues[real_name] = [clues_data]
            else:
                catalog_clues[real_name].append(clues_data)
        if clues_data[4]:
            for alt_name in clues_data[4]:
                if not state:
                    alt_name = "%s$%s" % (alt_name, state_short_name)
                if alt_name not in catalog_clues:
                    catalog_clues[alt_name] = [clues_data]
                else:
                    catalog_clues[alt_name].append(clues_data)


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter


def state_match(row, columns, collection):
    #ITZA: Hay que investigar cómo importar genérico con variable 'collection'
    from catalog.models import State
    query_filter = build_query_filter(row, columns)
    #ITZA: Investigar nombramiento genérico
    state = State.objects.filter(**query_filter).first()
    return state


def delegation_match(row, columns, collection):
    from catalog.models import Delegation
    query_filter = build_query_filter(row, columns)
    delegation = Delegation.objects.filter(**query_filter).first()
    return delegation


class MatchesMix:

    def build_csv_converted(self, task_params=None):
        from datetime import datetime
        import uuid
        from inai.models import NameColumn, Transformation
        from formula.models import MissingRow, Prescription
        from scripts.common import get_file, start_session

        data_file = self
        file_control = self.petition_file_control.file_control
        name_columns = NameColumn.objects.filter(
            file_control=file_control)
        original_columns = name_columns.filter(
            position_in_data__isnull=False)
        delegation_columns = name_columns.filter(
            final_field__collection__model_name='Delegation')
        if not delegation_columns.exists():
            return [], [], None
        all_missing_rows = []
        delimiter = file_control.delimiter or ','
        columns_count = original_columns.count()

        def divide_row_data(curr_row, row_seq=None):
            row_data = curr_row.split(delimiter) if delimiter else curr_row
            if len(row_data) == columns_count:
                return row_data
            else:
                # MissingRow.objects.create()
                current_error = "conteo extraño: %s columnas" % len(row_data)
                all_missing_rows.append({
                    "row_seq": row_seq,
                    "original_data": row_data,
                    "errors": current_error
                })
                print(current_error)
            return None

        prescription_fields = Prescription._meta.get_fields()
        field_names = [field.name for field in prescription_fields]
        print("field_names", field_names, "\n\n")

        s3_client, dev_resource = start_session()
        complete_file = get_file(data_file, dev_resource)

        data_rows = complete_file.readlines()
        column_folio = name_columns.filter(
            final_field__name='folio_document').first()

        simple_fields = [
            {
                "final_field__name": "name",
                "final_field__collection__model_name": "DocumentType",
                "name_in_prescription": "type_document"
            },
            {
                "final_field__name": "prescribed_amount",
                "final_field__parameter_group__name": "Cantidades en Recetas",
                "name_in_prescription": "prescribed_amount"
            },
            {
                "final_field__name": "delivered_amount",
                "final_field__parameter_group__name": "Cantidades en Recetas",
                "name_in_prescription": "delivered_amount"
            },
            {
                "final_field__name": "budget_key",
                "name_in_prescription": "budget_key"
            },
        ]
        existing_simple_fields = []
        for simple_field in simple_fields:
            name_in_prescription = simple_field.pop("name_in_prescription")
            print("simple_field", simple_field)
            current_column = name_columns.filter(**simple_field).first()
            if current_column:
                print("EXITOOOO", current_column)
                locals()[f"{name_in_prescription}_column"] = current_column
                existing_simple_fields.append(name_in_prescription)

        column_date = None
        transformation_date = None
        date_fields = ['date_release', 'date_visit', 'date_delivery']
        for date_field in date_fields:
            current_date = name_columns.filter(
                final_field__name=date_field).first()
            if current_date:
                locals()[f"{date_field}_column"] = current_date
                existing_simple_fields.append(date_field)
                column_date = current_date
                if transformation_date:
                    continue
                transformation = Transformation.objects.filter(
                    name_column=current_date, clean_function__name="format_date").first()
                if transformation:
                    transformation_date = transformation

        string_date = '%Y-%m-%d'
        try:
            string_date = transformation_date.addl_params["value"]
        except Exception:
            pass

        if not column_date or not column_folio:
            error = "No se encontró ninguna columna de fecha o folio"
            return [], [error], None

        last_date = None
        iso_date = None
        first_iso = None
        all_prescriptions = { }
        all_prescriptions_list = []
        provisional_list = []
        print("string_date: ", string_date)
        data_rows = data_rows[file_control.row_start_data:]
        for seq, row in enumerate(data_rows, start=file_control.row_start_data):
            data_row = row.decode('latin-1').replace('\r\n', '')
            data_row = divide_row_data(data_row, row_seq=seq)
            # print("data_row \t", data_row)
            date = data_row[column_date.position_in_data-1]
            if last_date != date[:10]:
                last_date = date[:10]
            folio_document = data_row[column_folio.position_in_data-1]
            curr_date = datetime.strptime(last_date, string_date)
            iso_date = curr_date.isocalendar()
            iso_year = iso_date[0]
            iso_week = iso_date[1]
            iso_day = iso_date[2]
            month = curr_date.month
            if not first_iso:
                first_iso = iso_date
            uuid_value = str(uuid.uuid4())
            folio_ocamis = "%s-%s-%s" % (iso_date[0], iso_date[1], folio_document)
            delivered = "unknown"
            quantities_columns = name_columns.filter(
                final_field__parameter_group__name='Cantidades en Recetas')
            quantities_fields = ["prescribed_amount", "delivered_amount"]
            for field in quantities_fields:
                field_column = quantities_columns.filter(
                    final_field__name=field).first()
                locals()[field] = data_row[field_column.position_in_data-1]
            if seq == 4:
                print("\n", "data_row", data_row, "\n")
            for simple_field in existing_simple_fields:
                current_column = locals()[f"{simple_field}_column"]
                locals()[simple_field] = data_row[current_column.position_in_data-1]
                if seq == 4:
                    print(
                        f"({current_column.position_in_data - 1})",
                        simple_field, "-->", locals()[simple_field])
                    print(f"-->{data_row[current_column.position_in_data-1]}<--")
            delivered_amount_2 = locals().get("delivered_amount")
            prescribed_amount_2 = locals().get("prescribed_amount")
            if prescribed_amount_2 and delivered_amount_2:
                if prescribed_amount_2 == delivered_amount_2:
                    delivered = "complete"
                elif prescribed_amount_2 < delivered_amount_2:
                    delivered = "partial"
                elif not delivered_amount_2:
                    delivered = "denied"

            delegation = None
            clues = None
            area = None
            # type_document = None
            doctor = None

            current_prescription_data = []
            current_provisional_data = {}
            for field_name in field_names:
                all_prescriptions[folio_ocamis] = True
                if field_name == "uuid":
                    value = uuid_value
                else:
                    value = locals().get(field_name)
                current_prescription_data.append(value)
                current_provisional_data[field_name] = value
            all_prescriptions_list.append(current_prescription_data)
            provisional_list.append(current_provisional_data)
            if len(all_prescriptions_list) > 20:
                break

        return [], [], provisional_list

    def build_catalogs(self):
        from inai.models import NameColumn
        from data_param.models import FinalField
        global columns
        global institution
        global state
        global petition
        catalog_clues = {}
        catalog_state = {}
        catalog_delegation = {}
        claves_medico_dicc = {}
        columns = {}
        institution = None
        state = None        
        petition = self.petition_file_control.petition
        institution = petition.entity.institution
        state = petition.entity.state
        #Se obtienen las variables que forman parte del data_file actual:
        current_fields = FinalField.objects.filter(
            name_column__file_control__petition_file_control__data_file=self)
        recipe_fields = current_fields.filter(
            collection__model_name='Prescription').values()
        drug_fields = current_fields.filter(
            collection__model_name='Drug').values()
        all_columns = NameColumn.objects.filter(
            file_control=self.petition_file_control.file_control)
        columns["all"] = all_columns.values()
        columns["clues"] = all_columns.filter(
            final_field__parameter_group='CLUES y Geográfico').values()
        columns["state"] = all_columns.filter(
            final_field__collection='State').values()
        columns["delegation"] = all_columns.filter(
            final_field__collection='Delegation').values()
        #RICK, evaluar la segunda condición:
        if not state and columns["state"]:
            build_catalog_state()
        if columns["delegation"]:
            build_catalog_delegation()
        build_catalog_clues()
        # for collection, collection_name in collections.items():
        #     columns[collection] = all_columns.filter(
        #         final_field__collection=collection_name).values('name')
