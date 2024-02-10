
class BuildSpendGroups:

    def __init__(self, activities):
        self.activities = activities
        self.all_activities = []
        self.spend_groups = []
        self.last_group = None

    def append_group(self):
        if self.last_group:
            group = self.last_group
            seconds = (group["end"] - group["start"]).seconds
            group["seconds"] = seconds
            self.spend_groups.append(group)

    def set_last_group(self, activity):
        self.last_group = {
            "start": activity["real_start"],
            "end": activity["real_end"],
        }

    def build_spend_groups(self):
        for activity in self.activities:
            if not self.last_group:
                self.set_last_group(activity)
            elif activity["real_start"] > self.last_group["end"]:
                self.append_group()
                self.set_last_group(activity)
            else:
                if activity["real_end"] > self.last_group["end"]:
                    self.last_group["end"] = activity["real_end"]
        self.append_group()
        self.clean_activities()
        # self.rebuild_spend_groups()
        return self.activities, self.spend_groups

    def rebuild_spend_groups(self):
        spend_groups = self.spend_groups.copy()
        self.spend_groups = []
        self.last_group = None
        for group in spend_groups:
            if not self.last_group:
                self.last_group = group
            elif group["start"] < self.last_group["end"]:
                self.last_group["end"] = group["end"]
            else:
                self.append_group()
                self.last_group = group
        self.append_group()

    def clean_activities(self):
        for activity in self.activities:
            del activity["real_start"]
            del activity["real_end"]
        return self.activities
