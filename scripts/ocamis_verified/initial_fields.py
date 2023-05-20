
def generate_months():
    from inai.models import EntityMonth
    from geo.models import Entity
    # for agency in Agency.objects.all():
    for entity in Entity.objects.all():
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = f"{year}-{month:02d}"
                EntityMonth.objects.get_or_create(
                    entity=entity, year_month=ye_mo)
                # print("%s-%s" % (agency.id, ye_mo))


def generate_months_one_year(year):
    from inai.models import EntityMonth
    from geo.models import Entity
    for agency in Entity.objects.all():
        for month in range(12):
            month += 1
            ye_mo = f"{year}-{month:02d}"
            EntityMonth.objects.get_or_create(
                year_month=ye_mo,
                entity=agency.entity)
            #print("%s-%s" % (agency.id, ye_mo))


def generate_months_agency(acronym):
    from inai.models import EntityMonth
    from geo.models import Entity
    for entity in Entity.objects.filter(acronym=acronym):
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = f"{year}-{month:02d}"
                EntityMonth.objects.get_or_create(
                    entity=entity, year_month=ye_mo)
                #print("%s-%s" % (agency.id, ye_mo))

#generate_months_agency("SSEDOMEX")
#generate_months_agency("CRAE")
#generate_months_agency("SSPCDMX")

        
def insert_populations():
    from geo.models import Agency
    pob_states2 = [
        ["01", 955242],
        ["02", 1195226],
        ["03", 565657],
        ["04", 603397],
        ["05", 611034],
        ["06", 492843],
        ["07", 4787898],
        ["08", 2147782],
        ["09", 6521002],
        ["10", 962129],
        ["11", 5237717],
        ["12", 5603620],
        ["13", 3283571],
        ["14", 2906439],
        ["15", 15647621],
        ["16", 2560437],
        ["17", 1149061],
        ["18", 626737],
        ["19", 2158032],
        ["20", 2646110],
        ["21", 5519115],
        ["22", 1784741],
        ["23", 1212873],
        ["24", 2079788],
        ["25", 1804068],
        ["26", 1283074],
        ["27", 1718981],
        ["28", 2623878],
        ["29", 1414381],
        ["30", 4993018],
        ["31", 1824086],
        ["32", 1455943],
        ]
    for pob_st in pob_states2:
        agencies = Agency.objects.filter(
            state__inegi_code=pob_st[0], clues__isnull=True)
        agencies.update(population=pob_st[1])
