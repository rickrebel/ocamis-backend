
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

    
def insert_populations():
    from catalog.models import Entity

    pob_states = [
        ["01", 271996],
        ["02", 515855],
        ["03", 139342],
        ["04", 327334],
        ["05", 181821],
        ["06", 179704],
        ["07", 2538415],
        ["08", 688684],
        ["09", 1203824],
        ["10", 404554],
        ["11", 2181882],
        ["12", 1744754],
        ["13", 1097048],
        ["14", 1213421],
        ["15", 3449337],
        ["16", 1372093],
        ["17", 618457],
        ["18", 346383],
        ["19", 558212],
        ["20", 1901352],
        ["21", 2721081],
        ["22", 587007],
        ["23", 383986],
        ["24", 961896],
        ["25", 629386],
        ["26", 465170],
        ["27", 794894],
        ["28", 735690],
        ["29", 531286],
        ["30", 2828959],
        ["31", 628098],
        ["32", 640844],
        ]

    for pob_st in pob_states:
        entities = Entity.objects.filter(
            state__inegi_code=pob_st[0], clues__isnull=True)
        entities.update(population=pob_st[1])
