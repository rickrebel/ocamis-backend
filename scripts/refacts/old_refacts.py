
def categorize_clean_functions():
    from data_param.models import CleanFunction
    valid_control_trans = [
        "include_tabs_by_name", "exclude_tabs_by_name",
        "include_tabs_by_index", "exclude_tabs_by_index",
        "only_cols_with_headers", "no_valid_row_data"]
    CleanFunction.objects.filter(
        name__in=valid_control_trans).update(ready_code="ready")
    valid_column_trans = [
        "fragmented", "concatenated", "format_date", "clean_key_container",
        "get_ceil", "only_params_parent", "only_params_child",
        "global_variable", "text_nulls", "almost_empty", "same_separator",
        "simple_regex"]
    CleanFunction.objects.filter(
        name__in=valid_column_trans).update(ready_code="ready")
    functions_alone = [
        "fragmented", "concatenated", "only_params_parent",
        "only_params_child", "text_nulls", "same_separator",
        "simple_regex", "almost_empty", "format_date"]
    CleanFunction.objects.filter(
        name__in=functions_alone).update(ready_code="ready_alone")


def assign_provider_to_data_files():
    from geo.models import Provider
    from respond.models import DataFile
    all_providers = Provider.objects.all()
    for provider in all_providers:
        data_files = DataFile.objects.filter(
            petition_file_control__petition__agency__provider=provider)
        data_files.update(provider=provider)
