
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

