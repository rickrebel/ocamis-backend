
class PetitionTransformsMix:
    agency: None

    def find_matches_in_children(
            self, all_data_files, current_file_ctrl=None, task_params=None):

        from scripts.common import get_readeable_suffixes
        from data_param.models import FileControl

        # self.__module__
        # cls = self.__class__
        # print("comienza find_matches_in_children", "\n")
        agency_file_controls = FileControl.objects.filter(
            petition_file_control__petition__agency=self.agency,
            file_format__isnull=False) \
            .exclude(data_group_id="orphan") \
            .prefetch_related("columns") \
            .distinct()
        all_errors = []
        all_tasks = []

        if current_file_ctrl:
            agency_file_controls = agency_file_controls.filter(
                id=current_file_ctrl)

        near_file_controls = agency_file_controls\
            .filter(petition_file_control__petition=self)\
            .prefetch_related("file_format")
        others_file_controls = agency_file_controls\
            .exclude(petition_file_control__petition=self)\
            .prefetch_related("file_format")
        all_file_controls = near_file_controls | others_file_controls

        for data_file in all_data_files:
            ctrl_list = list(all_file_controls.values_list("id", flat=True))
            curr_kwargs = {
                "after_if_empty": "find_matches_in_file_controls",
                "after_params_if_empty": {
                    "all_file_controls_ids": ctrl_list
                },
                "current_file_ctrl": current_file_ctrl,
                "all_tasks": all_tasks,
                "all_errors": all_errors,
            }

            all_tasks, all_errors, data_file = data_file.get_sample_data(
                task_params, **curr_kwargs)
            # print("Nuevos tasks y errors:", "\n", all_tasks, "\n", all_errors, "\n")
            if all_tasks or all_errors:
                continue
            task_params["models"] = [data_file]
            new_body = {
                "all_file_controls": all_file_controls,
                "petition": self
            }
            data_file.find_matches_in_file_controls(
                task_params=task_params, **new_body)

        return all_tasks, all_errors
