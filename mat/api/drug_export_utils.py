from django.apps import apps
from geo.models import Provider
from medicine.models import Group as TherapeuticGroup, Component
from typing import Any, Optional


prev_iso = "week_record__"
comp_string = "medicament__container__presentation__component"
first_values = {
    'year': f'{prev_iso}year',
    'month': f'{prev_iso}month',
}


class DrugExport:
    provider_id: int
    component_id: int
    # therapeutic_group_id: int | None
    therapeutic_group_id: Optional[int]

    def __init__(
            self,
            req_data: dict,
            by_delegation: bool = False,
    ):

        self.provider_id = req_data.get("provider_id")
        self.component_id = req_data.get("component_id")
        self.therapeutic_group_id = req_data.get("therapeutic_group_id")
        self.has_delegation = req_data.get("has_delegation")
        self.delegation_id = req_data.get("delegation_id")
        self.container_id = req_data.get("container_id")
        self.presentation_id = req_data.get("presentation_id")
        self.components_ids = req_data.get("components_ids", [])
        self.by_delegation = by_delegation
        self.prefetches = []
        self.is_total = False
        self.display_headers = {
            "provider": "Institución proveedora",  # Provider.acronym
            "therapeutic_group": "Grupo terapeútico",  # TherapeuticGroup.name
            "component": "Componente",  # Component.name
            "year": "año",
            "month": "mes",
            "year_week": "Semana y año epidemiológico (yyyy-ww)",
            "prescribed": "Unidades prescritas",
            "delivered": "Unidades entregadas",
            "total": "Recetas",
        }
        self.model_fields = {
            "provider": (Provider, "acronym"),
            "therapeutic_group": (TherapeuticGroup, "name"),
            "component": (Component, "name"),
        }
        self._dict_data = {}
        self.first_values = first_values.copy()
        self.query_filter = {f"{prev_iso}iso_year__gte": 2017}

    def build_base_data(self, is_mini):
        self.prefetches = []
        if not is_mini:
            self.prefetches = ['week_record']

        # prev_iso = "" if is_mini else "week_record__"
        field_ent = f"{prev_iso}provider_id"

        if is_mini:
            field_comp = f"{comp_string}_id"
        else:
            field_comp = 'container__presentation__component_id'
        # else:  # not is_complex
        #     field_comp = 'component_id'
        self.first_values = first_values.copy()
        self.query_filter = {f"{prev_iso}iso_year__gte": 2017}
        return field_ent, field_comp

    def build_spiral_data(self, is_total=False, group_by=None):
        self.is_total = is_total
        is_complex = True
        is_mini = not is_total and not self.has_delegation
        self.first_values['iso_week'] = f'{prev_iso}iso_week'
        self.first_values['iso_year'] = f'{prev_iso}iso_year'

        field_ent, field_comp = self.build_base_data(is_mini)
        some_drug = self.container_id or self.presentation_id or self.component_id

        if self.provider_id:
            first_values['provider'] = field_ent
            self.query_filter[field_ent] = self.provider_id

        if group_by == 'provider':
            first_values['provider'] = field_ent
            if self.therapeutic_group_id and not is_total and not some_drug:
                first_values['therapeutic_group'] = f"{comp_string}__groups__id"
                self.query_filter[f'{comp_string}__groups__id'] = self.therapeutic_group_id
        elif self.by_delegation:
            first_values["delegation"] = "delegation_id"
        elif group_by == 'therapeutic_group':
            if not is_total:
                first_values['therapeutic_group'] = f"{comp_string}__groups__id"
                # self.query_filter[f'{comp_string}__groups__id'] = self.therapeutic_group_id
        elif group_by == 'component':
            if not is_total:
                if self.components_ids:
                    self.query_filter[f'{comp_string}__id__in'] = self.components_ids
                else:
                    self.query_filter[f'{comp_string}__groups__id'] = self.therapeutic_group_id
                    self.query_filter[f'{comp_string}__priority__lt'] = 6
                first_values['component'] = field_comp

        prev_med = "medicament__" if is_mini else ""
        # container__presentation__component
        # container__presentation
        if is_total:
            pass
        # RICK Deshacer este orden
        elif self.container_id:
            self.query_filter[f'{prev_med}container_id'] = self.container_id
        elif self.presentation_id:
            if is_mini:
                field = 'medicament__container__presentation_id'
            elif is_complex:
                field = 'container__presentation_id'
            else:
                field = 'presentation_id'
            self.query_filter[field] = self.presentation_id
        elif self.component_id:
            if is_mini:
                field = 'medicament__container__presentation__component_id'
            elif is_complex:
                field = 'container__presentation__component_id'
            else:
                field = 'component_id'
            self.query_filter[field] = self.component_id

        final_query, _ = self.build_queries()
        return final_query

    def build_worksheet_data(self, worksheet_name="pestaña", is_total=False):
        # is_complex = is_total or bool(clues_id)
        self.is_total = is_total
        is_mini = not is_total and not self.has_delegation
        self.first_values['year_week'] = f'{prev_iso}year_week'
        field_ent, field_comp = self.build_base_data(is_mini)

        # if clues_id:
        #     query_filter['clues_id'] = clues_id
        # elif delegation_id:
        #     query_filter['delegation_id'] = delegation_id
        if self.provider_id:
            self.query_filter[field_ent] = self.provider_id

        self.first_values['provider'] = field_ent

        if is_mini:
            if not (self.therapeutic_group_id or self.component_id):
                self.first_values['therapeutic_group'] = f"{comp_string}__groups__id"
            if self.therapeutic_group_id:
                self.query_filter[f'{comp_string}__groups__id'] = self.therapeutic_group_id
            if self.therapeutic_group_id:
                self.first_values['component'] = field_comp
            if self.component_id:
                field = 'medicament__container__presentation__component_id'
                self.query_filter[field] = self.component_id

        mother_model_query, display_values = self.build_queries()

        worksheet_data = {
            "name": worksheet_name,
            "table_data": self.values_to_plane_table(
                mother_model_query, display_values),
            # "columns_width": None,
            # "columns_width_pixel": None,
            # "max_decimal": 1
        }

        return worksheet_data

    def build_queries(self):
        from django.db.models import Sum, F

        annotates = {
            'total': Sum('total'),
            'delivered': Sum('delivered_total'),
            'prescribed': Sum('prescribed_total'),
        }
        display_values = [v for v in annotates.keys()]
        for key, value in self.first_values.items():
            if key != value:
                annotates[key] = F(value)
            display_values.append(key)
        order_values = ["year", "month", "iso_year", "iso_week"]
        if self.by_delegation:
            order_values.insert(0, "delegation")
        # prev_model = "Mother" if is_big_active else "Mat"
        # model = "Totals" if is_total else "Priority"
        model = "Totals" if self.is_total else "Entity"
        model_name = f"MatDrug{model}2"
        # print("model_name: ", model_name)
        app_label = "formula"
        mother_model = apps.get_model(app_label, model_name)

        mother_model_query = mother_model.objects \
            .filter(**self.query_filter) \
            .prefetch_related(*self.prefetches) \
            .values(*self.first_values.values()) \
            .annotate(**annotates) \
            .values(*display_values) \
            .order_by(*order_values)

        return mother_model_query, display_values

    def values_to_plane_table(self, mother_model_query, headers):
        headers_data = [self.display_headers.get(
            header, header) for header in headers]
        data = [headers_data]
        for values in mother_model_query:
            rows_data = []
            for header in headers:
                row = values.get(header, "")
                if header in self.model_fields:
                    row = self.dict_data(header).get(row, row)
                rows_data.append(row)
            data.append(rows_data)
        return data

    def dict_data(self, collection):
        if not hasattr(self._dict_data, collection):
            base_model, field = self.model_fields.get(collection)
            self._dict_data[collection] = {
                item.id: getattr(item, field)
                for item in base_model.objects.all()
            }
        return self._dict_data[collection]
