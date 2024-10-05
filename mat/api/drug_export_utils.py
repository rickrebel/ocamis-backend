from django.apps import apps
from django.db.models import Sum, F


class DrugExport:
    provider_id: int
    component_id: int
    therapeutic_group_id: int | None

    def __init__(
            self, provider_id: int, component_id: int,
            therapeutic_group_id: int | None = None
    ):
        self.provider_id = provider_id
        self.component_id = component_id
        self.therapeutic_group_id = therapeutic_group_id
        self.display_headers = {
            "display_value": "Display Header"
        }

    def build_worksheet_data(self, worksheet_name="pestaña", is_total=False):
        prefetches = []
        if is_total:
            prefetches = ['week_record']

        # prev_iso = "" if is_mini else "week_record__"
        prev_iso = "week_record__"
        field_ent = f"{prev_iso}provider_id"
        first_values = {
            'iso_week': f'{prev_iso}iso_week',
            'iso_year': f'{prev_iso}iso_year',
            'year': f'{prev_iso}year',
            'month': f'{prev_iso}month',
            'provider': field_ent,
        }

        comp_string = "medicament__container__presentation__component"
        if not is_total:
            field_comp = f"{comp_string}_id"
        else:
            field_comp = 'container__presentation__component_id'

        query_filter = {f"{prev_iso}iso_year__gte": 2017}
        if self.provider_id:
            query_filter[field_ent] = self.provider_id

        if not is_total:
            if not (self.therapeutic_group_id or self.component_id):
                first_values['therapeutic_group'] = f"{comp_string}__groups__id"
            if self.therapeutic_group_id:
                query_filter[f'{comp_string}__groups__id'] = self.therapeutic_group_id
            if self.therapeutic_group_id:
                first_values['component'] = field_comp
            if self.component_id:
                field = 'medicament__container__presentation__component_id'
                query_filter[field] = self.component_id

        annotates = {
            'total': Sum('total'),
            'delivered': Sum('delivered_total'),
            'prescribed': Sum('prescribed_total'),
        }
        display_values = [v for v in annotates.keys()]
        for key, value in first_values.items():
            if key != value:
                annotates[key] = F(value)
            display_values.append(key)
        order_values = ["year", "month", "iso_year", "iso_week"]
        # prev_model = "Mother" if is_big_active else "Mat"
        # model = "Totals" if is_total else "Priority"
        model = "Totals" if is_total else "Entity"
        model_name = f"MatDrug{model}2"
        # print("model_name: ", model_name)
        app_label = "formula"
        mother_model = apps.get_model(app_label, model_name)

        mother_model_query = mother_model.objects \
            .filter(**query_filter) \
            .prefetch_related(*prefetches) \
            .values(*first_values.values()) \
            .annotate(**annotates) \
            .values(*display_values) \
            .order_by(*order_values)

        worksheet_data = {
            "name": worksheet_name,
            "table_data": self.values_to_plane_table(
                mother_model_query, display_values),
            # "columns_width": None,
            # "columns_width_pixel": None,
            # "max_decimal": 1
        }

        return worksheet_data

    def values_to_plane_table(self, mother_model_query, headers):
        headers_data = [self.display_headers.get(
            header, header) for header in headers]
        data = [headers_data]
        for values in mother_model_query:
            rows_data = []
            for header in headers:
                row = values.get(header, "")
                if header == "provider_id":
                    row = self.providers_data.get(row, row)
                rows_data.append(row)
            data.append(rows_data)
        return data

    @property
    def providers_data(self):
        if not hasattr(self, "_providers_data"):
            self._providers_data = {
            }
        return self._providers_data
