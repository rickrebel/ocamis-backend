
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



def generate_months_entity(acronym):
    from inai.models import MonthEntity
    from catalog.models import Entity
    for entity in Entity.objects.filter(acronym=acronym):
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = "%s%s%s" % (year, '0' if month < 10 else '', month)
                MonthEntity.objects.get_or_create(entity=entity, year_month=ye_mo)
                #print("%s-%s" % (entity.id, ye_mo))

#generate_months_entity("SSEDOMEX")
#generate_months_entity("CRAE")
#generate_months_entity("SSPCDMX")

    
def insert_populations():
    from catalog.models import Entity
    pob_states2 = [
        ["01", 512307],
        ["02", 716445],
        ["03", 298395],
        ["04", 383169],
        ["05", 2977123],
        ["06", 1404548],
        ["07", 4241851],
        ["08", 378543],
        ["09", 280046],
        ["10", 583001],
        ["11", 3320235],
        ["12", 1191436],
        ["13", 1993950],
        ["14", 1918004],
        ["15", 6244052],
        ["16", 1833109],
        ["17", 693751],
        ["18", 394656],
        ["19", 1297597],
        ["20", 1212935],
        ["21", 2434328],
        ["22", 1098890],
        ["23", 612069],
        ["24", 967405],
        ["25", 907298],
        ["26", 810761],
        ["27", 1434441],
        ["28", 1239802],
        ["29", 881099],
        ["30", 2277269],
        ["31", 1125157],
        ["32", 828382],
        ]
    for pob_st in pob_states2:
        entities = Entity.objects.filter(
            state__inegi_code=pob_st[0], clues__isnull=True)
        entities.update(population=pob_st[1])
