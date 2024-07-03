
def move_delegation_clues():
    from geo.models import Delegation, CLUES, Provider
    all_delegations = Delegation.objects.all()
    for delegation in all_delegations:
        clues = delegation.clues
        if clues:
            clues.delegation = delegation
            delegation.is_clues = True
            if clues.provider:
                delegation.provider = clues.provider
        elif not delegation.provider:
            try:
                delegation.provider = Provider.objects.get(
                    institution=delegation.institution,
                    state=delegation.state, ent_clues__isnull=True)
            except Provider.DoesNotExist:
                print("Provider not found: ", delegation)
            except Provider.MultipleObjectsReturned:
                print("Multiple delegations found: ", delegation)
        delegation.save()


def generate_agency_delegations():
    from geo.models import Delegation, Agency
    agencies_with_clues = Agency.objects.filter(clues__isnull=False).distinct()
    for agency in agencies_with_clues:
        name = f"{agency.name}"
        Delegation.objects.get_or_create(
            name=name, state=agency.state,
            institution=agency.institution, clues=agency.clues)


def create_provider_by_agency():
    from geo.models import Agency, Provider
    agencies = Agency.objects.all()
    for agency in agencies:
        if agency.clues:
            provider, created = Provider.objects.get_or_create(
                name=agency.name, acronym=agency.acronym, state=agency.state,
                institution=agency.institution,
                population=agency.population or 0, is_clues=True
            )
            clues = agency.clues
            clues.provider = provider
            clues.save()
        elif agency.state:
            provider, created = Provider.objects.get_or_create(
                state=agency.state, institution=agency.institution,
                is_clues=False)
            if created:
                provider.population = agency.population or 0
                state_code = agency.state.code_name.upper().replace(".", "")
                provider.acronym = f"SSA-{state_code}"
                provider.name = f"{agency.institution.name} {agency.state.short_name}"
                provider.save()
        else:
            provider, created = Provider.objects.get_or_create(
                name=agency.institution.name, acronym=agency.acronym,
                institution=agency.institution, population=agency.population or 0,
                is_clues=False)
        agency.provider = provider
        agency.save()


def assign_entity_to_delegations():
    from geo.models import Provider
    from geo.models import Delegation
    all_delegations = Delegation.objects.filter(
        provider__isnull=True, is_clues=False)
    for delegation in all_delegations:
        institution = delegation.institution
        try:
            provider = Provider.objects.get(institution=institution)
            delegation.provider = provider
            delegation.save()
        except Exception as e:
            print(e)
