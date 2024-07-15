from inai.models import Petition
from task.base_views import TaskBuilder
from task.helpers import HttpResponseError


class PetitionTransformsMixReal:

    def __init__(self, petition: Petition, base_task: TaskBuilder = None):
        self.petition = petition
        self.task_params = {"parent_task": base_task.main_task}
        self.base_task = base_task

    # Función after y directa
    def find_matches_for_data_files(self, all_data_files, file_control_id=None):

        from data_param.models import FileControl
        from data_param.views import get_related_file_controls
        from respond.data_file_mixins.explore_mix_real import ExploreRealMix

        if file_control_id:
            provider_file_controls = FileControl.objects.filter(id=file_control_id)
        else:
            provider_file_controls = get_related_file_controls(
                petition=self.petition)

        provider_ctrl_list = list(
            provider_file_controls.values_list("id", flat=True))

        for data_file in all_data_files:
            curr_kwargs = {
                # RICK TASK: No contemplamos task_kwargs_if_empty en ningún lugar
                "task_kwargs": {
                    "function_after": "find_matches_between_controls",
                    "params_after": {"provider_controls_ids": provider_ctrl_list},
                },
                "after_if_empty": "find_matches_between_controls",
                "after_params_if_empty": {
                    "provider_controls_ids": provider_ctrl_list
                },
            }
            explore = ExploreRealMix(
                data_file, base_task=self.base_task, want_response=True)
            if data_file.sheet_names_list:
                pass
            else:
                try:
                    explore.get_sample_data(
                        current_file_ctrl=file_control_id, **curr_kwargs)
                except HttpResponseError:
                    continue
            new_task_params = self.task_params.copy()
            new_task_params["models"] = [data_file]

            explore.find_matches_between_controls(
                task_params=new_task_params,
                provider_file_controls=provider_file_controls)

        self.base_task.comprobate_status()
