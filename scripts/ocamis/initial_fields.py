
def generate_months():
    from inai.models import MonthEntity
    from catalog.models import Entity
    for entity in Entity.objects.all():
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = "%s%s%s" % (year, '0' if month < 10 else '', month)
                MonthEntity.objects.get_or_create(entity=entity, year_month=ye_mo)
                #print("%s-%s" % (entity.id, ye_mo))
