
import unidecode

raws = {}

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


class MatchesMix:

    def build_catalogs(self):
        return False
        from inai.models import NameColumn
        global columns
        global institution
        global state
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
        droug_fields = current_fields.filter(
            collection__model_name='Droug').values()        
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
