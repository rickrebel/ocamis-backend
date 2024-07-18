from inai.models import Petition
from respond.models import DataFile
from data_param.models import FileControl
from task.builder import TaskBuilder
from task.helpers import HttpResponseError


class PetitionTransformMix:

    def __init__(self, petition: Petition, data_files,
                 base_task: TaskBuilder = None):
        self.petition = petition
        self.base_task = base_task
        self.data_files = data_files
        self.curr_kwargs = {}

    # Función directa
    def find_matches_for_data_files(self):
        self.curr_kwargs = {"function_after": "find_matches_between_controls"}
        for data_file in self.data_files:
            explore = self._get_explore_sample(data_file)
            if explore:
                try:
                    explore.find_matches_between_controls()
                except HttpResponseError:
                    continue

        self.base_task.comprobate_status()

    # Función directa
    def match_direct_for_data_files(self, file_control: FileControl):

        self.curr_kwargs = {
            "function_after": "find_matches_in_control",
            "file_control_id": file_control.id
        }

        for data_file in self.data_files:
            explore = self._get_explore_sample(data_file)
            if explore:
                try:
                    explore.find_matches_in_control(file_control)
                except HttpResponseError:
                    continue

        self.base_task.comprobate_status()

    def _get_explore_sample(self, data_file: DataFile):
        from respond.data_file_mixins.explore_mix import ExploreRealMix

        explore = ExploreRealMix(
            data_file, base_task=self.base_task, want_response=True)
        if not data_file.sheet_names_list:
            try:
                explore.get_sample_data(**self.curr_kwargs)
            except HttpResponseError:
                return None
        return explore
