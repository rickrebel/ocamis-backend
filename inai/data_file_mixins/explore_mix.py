from category.models import StatusControl
import unidecode
from data_param.models import FinalField
from category.models import StatusControl


def build_catalog_delegation():
    from catalog.models import Delegation
    global catalog_delegation
    #RICK Evaluar si es necesario declarar global acá:
    global state
    global institution
    curr_delegations = Delegation.objects.filter(institution=institution)
    if state:
        curr_delegations = curr_delegations.filter(state=state)
    delegs_query = list(curr_delegations.values_list(
        'name', 'other_names', 'state__short_name'))
    for deleg in delegs_query:
        try:
            deleg_name = unidecode.unidecode(deleg[0]).upper()
        except Exception:
            deleg_name = deleg[0].upper()
        if deleg_name not in catalog_delegation:
            catalog_delegation[deleg_name] = [deleg]
        alt_names = deleg[1] or []
        for alt_name in alt_names:
            if alt_name not in catalog_delegation:
                catalog_delegation[alt_name] = [deleg]
            else:
                catalog_delegation[alt_name].append(deleg)


def build_catalog_state():
    from catalog.models import State
    global catalog_state
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
    global institution
    global state
    clues_data_query = CLUES.objects.filter(institution=institution)
    if state:
        clues_data_query.filter(state=state)
    clues_data_query = list(
        clues_data_query.values_list(
            "state__name", "name", "tipology_cve",
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
            prov_name = u"%s %s" % (cve, clues_name)
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


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter



class ExploreMix:

    def get_table_ref(self):
        print(self)
        return 2

    def start_file_process(self, is_explore=False):
        print("IS EXPLOREEEE ", is_explore)
        from rest_framework.response import Response
        from rest_framework import (permissions, views, status)        
        from category.models import StatusControl
        #FieldFile.open(mode='rb')
        recipe_fields = FinalField.objects.filter(
            collection__model_name='Prescription').values()
        droug_fields = FinalField.objects.filter(
            collection__model_name='Droug').values()
        catalog_clues = {}
        catalog_state = {}
        catalog_delegation = {}
        claves_medico_dicc = {}
        columns = {}
        institution = None
        state = None
        import json
        self.error_process = []
        self.save()
        count_splited, errors, suffix = self.split_and_decompress()

        if errors:
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
            return self.save_errors(errors, status_error)
        if count_splited and not is_explore:
            warnings = [("Son muchos archivos y tardarán en"
                " procesarse, espera por favor")]
            return Response(
                {"errors": warnings}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if not is_explore:
            self.build_catalogs()
        elif count_splited:
            #FALTA AFINAR FUNCIÓN PARA ESTO
            for ch_file in self.child_files:
                data = ch_file.transform_file_in_data(is_explore, suffix)
        else:
            print("HOLA TERMINO")
            data = self.transform_file_in_data(is_explore, suffix)
            print("HOLA TERMINO2")
        if is_explore:
            print(data["headers"])
            print(data["structured_data"][:6])
            return data

        return data

    def build_catalogs(self):
        from inai.models import NameColumn
        global columns
        global institution
        global state
        petition = self.petition_file_control.petition
        institution = petition.entity.institution
        state = petition.entity.state
        all_columns = NameColumn.objects.filter(
            file_control=self.petition_file_control.file_control)
        columns["all"] = all_columns.values()
        columns["clues"] = all_columns.filter(
            final_field__collection='CLUES').values()
        columns["state"] = all_columns.filter(
            final_field__collection='CLUES').values()
        build_catalog_delegation()
        #RICK, evaluar la segunda condición:
        if not state and columns["state"]:
            build_catalog_state()
        build_catalog_clues()
        for collection, collection_name in collections.items():
            columns[collection] = all_columns.filter(
                final_field__collection=collection_name).values_list('name')


    #def split_file(path="G:/My Drive/YEEKO/Clientes/OCAMIS/imss"):
    def split_file(self):
        from filesplit.split import Split
        from inai.models import File
        [directory, only_name] = self.file_name.rsplit("/", 1)
        [base_name, extension] = only_name.rsplit(".", 1)
        curr_split = Split(self.file_name, directory)
        curr_split.bylinecount(linecount=1000000)
        initial_status = StatusControl.objects.get_or_create(
            name='initial')
        count_splited = 0
        original_file = self.origin_file or self
        for file_num in range(99):
            rr_file_name = "%s_%s.%s" % (base_name, file_num + 1, extension)
            if not os.path.exists(rr_file_name):
                print("Invalid path", rr_file_name)
                break
            if not os.path.isfile(reporte_recetas_path):
                print("Invalid path")
                break
            new_file = File.objects.create(
                self=rr_file_name,
                origin_file=original_file,
                date=original_file.date,
                status=initial_status,
                #Revisar si lo más fácil es poner o no los siguientes:
                #file_control=original_file.file_control,
                file_control=original_file.petition_file_control.file_control,
                petition=original_file.petition,
                petition_month=original_file.petition_month)
            count_splited += 1
        if count_splited > 0:
            if self.origin_file:
                self.delete()
            first_file_name = "%s_%s.%s" % (base_name, 1, extension)
            first_file = File.objects.get(file=first_file_name)
            return first_file, count_splited
        else:
            return self, 0

