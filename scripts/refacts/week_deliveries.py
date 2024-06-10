# zero = models.IntegerField(blank=True, null=True)
# unknown = models.IntegerField(blank=True, null=True)
# unavailable = models.IntegerField(blank=True, null=True)
# partial = models.IntegerField(blank=True, null=True)
# over_delivered = models.IntegerField(blank=True, null=True)
# error = models.IntegerField(blank=True, null=True)
# denied = models.IntegerField(blank=True, null=True)
# complete = models.IntegerField(blank=True, null=True)
# cancelled = models.IntegerField(blank=True, null=True)
# big_denied = models.IntegerField(blank=True, null=True)
# big_partial = models.IntegerField(blank=True, null=True)
all_deliveries = [
    "zero", "unknown", "unavailable", "partial", "over_delivered",
    "error", "denied", "complete", "cancelled", "big_denied", "big_partial"
]


def move_all_deliveries():
    from respond.models import WeekRecord
    from inai.models import DeliveredWeek
    new_delivery_weeks = []
    all_weeks = WeekRecord.objects.filter(rx_count__gt=0)
    for week in all_weeks:
        sums_by_delivered = {}
        for delivery_key in all_deliveries:
            count = getattr(week, delivery_key)
            if count:
                new_delivery = DeliveredWeek(
                    week_record=week, delivered_id=delivery_key, value=count)
                new_delivery_weeks.append(new_delivery)
                sums_by_delivered[delivery_key] = count
    DeliveredWeek.objects.bulk_create(new_delivery_weeks)
