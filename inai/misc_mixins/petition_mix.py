from inai.models import Petition
from task.base_views import TaskBuilder


class FromAws:

    def __init__(self, petition: Petition, task_params=None,
                 base_task: TaskBuilder = None):
        self.petition = petition
        self.agency = petition.agency
        self.task_params = task_params
