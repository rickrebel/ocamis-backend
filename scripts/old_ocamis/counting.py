# def every_has_total_rows(self, task_params=None, **kwargs):
#     data_file = self
#     sample_data = data_file.sample_data
#     need_recalculate = False
#     if not sample_data:
#         need_recalculate = True
#     if not need_recalculate:
#         for sheet_name, sheet_data in sample_data.items():
#             if not sheet_data.get("total_rows"):
#                 need_recalculate = True
#                 break
#     if need_recalculate:
#         curr_kwargs = {
#             "forced_save": True, "after_if_empty": "counting_from_aws"}
#         all_tasks, all_errors, data_file = data_file.get_sample_data(
#             task_params, **curr_kwargs)
#         return all_tasks, all_errors, data_file
#     return [], [], data_file

# def counting_from_aws(self, task_params=None, **kwargs):
#     from data_param.models import FileControl
#     data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
#     data_file, saved, errors = data_file.find_coincidences()
#     if not saved and not errors:
#         errors = ["No coincide con el formato del archivo (counting)"]
#     if errors:
#         data_file.save_errors(errors, "explore_fail")
#     return [], errors, None
