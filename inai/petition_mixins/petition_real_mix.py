from inai.models import Petition
from task.base_views import TaskBuilder


class PetitionTransformsMixReal:

    def __init__(self, petition: Petition, base_task: TaskBuilder = None):
        self.petition = petition
        self.task_params = {"parent_task": base_task.main_task}
        self.base_task = base_task

    def find_matches_in_children(
            self, all_data_files, current_file_ctrl=None):

        from data_param.models import FileControl

        agency_file_controls = FileControl.objects.filter(
            petition_file_control__petition__agency=self.petition.agency,
            file_format__isnull=False) \
            .exclude(data_group_id="orphan") \
            .prefetch_related("columns") \
            .distinct()

        if current_file_ctrl:
            agency_file_controls = agency_file_controls.filter(
                id=current_file_ctrl)

        near_file_controls = agency_file_controls \
            .filter(petition_file_control__petition=self) \
            .prefetch_related("file_format")
        others_file_controls = agency_file_controls \
            .exclude(petition_file_control__petition=self) \
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
            }

            all_tasks, all_errors, data_file = data_file.get_sample_data(
                self.task_params, **curr_kwargs)
            if all_tasks or all_errors:
                if all_errors:
                    self.base_task.add_errors(all_errors, True, comprobate=False)
                    continue
                if all_tasks:
                    self.base_task.add_many_tasks(all_tasks)
                    continue
            new_task_params = self.task_params.copy()
            new_task_params["models"] = [data_file]
            new_body = {
                "all_file_controls": all_file_controls,
                "petition": self
            }
            data_file.find_matches_in_file_controls(
                task_params=new_task_params, **new_body)

        self.base_task.comprobate_status()
