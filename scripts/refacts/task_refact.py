
def orphan_function_names():
    from classify_task.models import Stage
    from task.models import AsyncTask, TaskFunction
    final_function_names = set()
    function_list = TaskFunction.objects.all().values_list("name", flat=True)
    exclude_names = list(function_list)
    # .exclude(function_after__in=exclude_names)\
    finished_names = AsyncTask.objects\
        .filter(function_after__isnull=False)\
        .values_list("function_after", flat=True)\
        .distinct()
    unique_finished_names = set(finished_names)
    print("unique_finished_names", unique_finished_names)
    missing_names = unique_finished_names - set(function_list)
    print("missing_names", missing_names)
    for missing_name in unique_finished_names:
        print(missing_name)
        # TaskFunction.objects.create(
        #     name=missing_name,
        #     model_name="month_record",
        #     public_name=missing_name,
        #     is_active=False)
    final_function_names.update(missing_names)

    # stage_finished_names = Stage.objects\
    #     .filter(finished_function__isnull=False)\
    #     .exclude(finished_function__in=exclude_names)\
    #     .values_list("finished_function", flat=True)\
    #     .distinct()
    # unique_stage_finished_names = set(stage_finished_names)
    # missing_stage_names = unique_stage_finished_names - set(function_list)
    # print("missing_stage_names", missing_stage_names)
    # final_function_names.update(missing_stage_names)
    return final_function_names


def create_missing_stage():
    from task.models import TaskFunction
    TaskFunction.objects.create(
        name="revert_stages_after",
        model_name="month_record",
        public_name="revert_stages_after",
        is_active=False)


# check_success_insert
# indexing_temp_tables_after
# save_week_base_models_after
# save_new_split_files
# insert_temp_tables_after
# build_sample_data_after
# save_lap_cat_tables_after
# find_coincidences_from_aws
# rebuild_week_csv_after
# validate_temp_tables_after
# decompress_zip_aws_after
# analyze_uniques_after
# decompress_gz_after
# find_matches_in_file_controls
# build_csv_data_from_aws
# save_merged_from_aws


# No encontrados:
# finish_build_csv_data
# explore_data_xls_after
# counting_from_aws


def clean_real_alternatives(size=30, clean=False):
    from scripts.common import similar, text_normalizer
    from data_param.models import NameColumn
    name_columns = NameColumn.objects\
        .filter(alternative_names__isnull=False)[:size]
    real_same_count = 0
    distinct_count = 0
    for name_column in name_columns:
        alt_names = name_column.alternative_names or []
        some_distinct = False
        for alt_name in alt_names:
            std_name = text_normalizer(alt_name, True)
            if name_column.std_name_in_data != std_name:
                print("\nstd_name", std_name)
                print("std_name_in_data", name_column.std_name_in_data)
                some_distinct = True
        if some_distinct:
            distinct_count += 1
        else:
            name_column.alternative_names = None
            real_same_count += 1
    print("real_same_count", real_same_count)
    print("distinct_count", distinct_count)
    if clean:
        NameColumn.objects.bulk_update(name_columns, ["alternative_names"])


clean_real_alternatives(6000, True)

