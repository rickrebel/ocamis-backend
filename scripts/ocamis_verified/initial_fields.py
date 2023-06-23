
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


def generate_weeks():
    from inai.models import EntityMonth, EntityWeek
    from geo.models import Entity
    from datetime import timedelta, date
    # for agency in Agency.objects.all():
    for entity in Entity.objects.all():
        new_weeks = []
        already_weeks = EntityWeek.objects.filter(entity=entity)\
            .values('year_week', 'entity', 'year_month', 'iso_delegation')
        # space
        def add_new_weeks(
                init_week, last_week, year_int, ent_month, iso_delegation):
            ye_mo = ent_month.year_month
            year_by_ym, month_by_ym = ye_mo.split('-')
            for week in range(init_week, last_week + 1):
                year_week = f"{year_int}-{week:02d}"
                if not any(
                        d['year_week'] == year_week
                        and d['entity'] == entity.id
                        and d['year_month'] == ye_mo
                        and d['iso_delegation'] == iso_delegation
                        for d in already_weeks):
                    new_weeks.append(EntityWeek(
                        entity=entity,
                        entity_month=ent_month,
                        year_week=year_week,
                        iso_year=year_int,
                        iso_week=week,
                        year_month=ent_month.year_month,
                        year=int(year_by_ym),
                        month=int(month_by_ym),
                        iso_delegation=iso_delegation))
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(1, 13):
                year_month = f"{year}-{month:02d}"
                entity_month, created = EntityMonth.objects.get_or_create(
                    entity=entity, year_month=year_month)
                # space
                start_date = date(year, month, 1)
                start_week = start_date.isocalendar()[1]
                start_year = start_date.isocalendar()[0]
                # space
                is_december = month == 12
                next_month = 1 if is_december else month + 1
                next_year = year + (1 if is_december else 0)
                end_date = date(next_year, next_month, 1) - timedelta(days=1)
                end_week = end_date.isocalendar()[1]
                end_year = end_date.isocalendar()[0]
                # space
                same_year = start_year == end_year
                if entity.split_by_delegation:
                    all_delegation_ids = entity.delegations.values_list(
                        'id', flat=True)
                else:
                    all_delegation_ids = [None]
                for delegation_id in all_delegation_ids:
                    if same_year:
                        add_new_weeks(
                            start_week, end_week, start_year,
                            entity_month, delegation_id)
                    else:
                        last_day = date(start_year, 12, 28)
                        add_new_weeks(
                            start_week, last_day.isocalendar()[1], start_year,
                            entity_month, delegation_id)
                        first_day = date(end_year, 1, 1)
                        add_new_weeks(
                            first_day.isocalendar()[1], end_week, end_year,
                            entity_month, delegation_id)
        # space
        EntityWeek.objects.bulk_create(new_weeks)


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
