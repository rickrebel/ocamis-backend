from inai.models import EntityMonth


class FromAws:

    def __init__(self, entity_month: EntityMonth, task_params=None):
        self.entity_month = entity_month
        self.task_params = task_params

    def save_month_analysis(self, **kwargs):
        from django.db.models import Sum
        from django.utils import timezone
        sum_fields = ["drugs_count", "rx_count", "duplicates_count", "shared_count"]

        query_sums = [Sum(field) for field in sum_fields]
        result_sums = self.entity_month.weeks.all().aggregate(*query_sums)
        print("result_sums", result_sums)
        for field in sum_fields:
            setattr(self.entity_month, field, result_sums[field + "__sum"])
        self.entity_month.last_crossing = timezone.now()
        self.entity_month.save()

        return [], [], True
