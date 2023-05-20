from inai.models import Petition


class FromAws:

    def __init__(self, petition: Petition, task_params=None):
        self.petition = petition
        self.agency = petition.agency
        self.task_params = task_params
