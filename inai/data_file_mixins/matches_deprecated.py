# ######## DEPRECATED #########
def build_catalog_state(self):
    from geo.models import State
    import unidecode
    catalog_state = { }
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


def build_catalogs_prev(self, columns):
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


def build_catalog_clues(self):
    # RICK 16: adaptar a CLAVE CLUES POR LO PRONTO, también key_issste
    from geo.models import CLUES
    import unidecode

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


def state_match(self, row, columns, collection):
    return row


def save_list_in_s3(self, list_to_save, list_name):
    return 2
