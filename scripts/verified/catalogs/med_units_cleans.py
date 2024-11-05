
def update_delegation_in_med_units(provider_id):
    from med_cat.models import MedicalUnit
    from geo.models import Delegation, Provider
    from scripts.common import text_normalizer
    from geo.views import build_catalog_delegation_by_id
    provider = Provider.objects.get(id=provider_id)
    dict_delegations = build_catalog_delegation_by_id(provider.institution)
    all_medical_units = MedicalUnit.objects.filter(
        provider=provider, delegation__isnull=True, delegation_name__isnull=False)
    print("all_medical_units", all_medical_units.count())
    for medical_unit in all_medical_units:
        delegation_name = text_normalizer(medical_unit.delegation_name)
        if delegation_name in dict_delegations:
            try:
                delegation_id = dict_delegations[delegation_name]
                delegation_found = Delegation.objects.get(id=delegation_id)
                if delegation_found.is_clues:
                    first_clues = delegation_found.all_clues.first()
                    if first_clues:
                        medical_unit.clues = first_clues
                    else:
                        print("delegation without clues", delegation_found)
                if "UMAE " in delegation_name:
                    delegation_id = dict_delegations["TODAS LAS UMAES"]
                medical_unit.delegation_id = delegation_id
                medical_unit.save()
            except Exception as e:
                print("error", e)
                print("delegation_name", delegation_name)
        elif provider.acronym == "ISSSTE":
            try:
                print("soy ISSSTE")
                if medical_unit.clues:
                    delegation_id = dict_delegations["HOSPITALES TERCER NIVEL"]
                    medical_unit.delegation_id = delegation_id
                    medical_unit.save()
            except Exception as e:
                print("error", e)
                print("delegation_name", delegation_name)
        else:
            print("medical_unit", medical_unit)
            print("delegation not found", delegation_name)


# update_delegation_in_med_units(53)


def update_clues(field_in_unit, field_in_clues):
    from med_cat.models import MedicalUnit
    from geo.models import CLUES
    med_units = MedicalUnit.objects.filter(clues__isnull=True)
    success_count = 0
    errors = {
        "CLUES no encontrada": [], "Multiples CLUES": [],
        "Otros errores": []}
    fields_in_unit_isnull = f"{field_in_unit}__isnull"  # clues__isnull , key_issste__isnull
    current_med_units = med_units.filter(**{fields_in_unit_isnull: False})
    for unit in current_med_units:
        elem_value = getattr(unit, field_in_clues)
        try:
            query_get = {field_in_clues: elem_value}
            value_to_assign = CLUES.objects.get(**query_get)
            unit.clues = value_to_assign
            success_count += 1
            unit.save()
        except CLUES.DoesNotExist:
            errors["CLUES no encontrada"].append(unit)
        except CLUES.MultipleObjectsReturned:
            errors["Multiples CLUES"].append(unit)
        except Exception as e:
            print("e", e)
            errors["Otros errores"].append(unit)
    print("Casos exitosos:", success_count)
    return errors


def reporte_clues():
    # fields = [["clues", "clues_key"], ["key_issste", "key_issste"]]
    errors_clues = update_clues("key_issste", "key_issste")
    error_count = 0
    for key, values in errors_clues.items():
        error_count += len(values)
        if len(values) > 0:
            print(key, len(values))
    print("Conteo total de errores:", error_count)
    return errors_clues


# all_errors = reporte_clues()


query_remain_issste = """
SELECT * FROM public.med_cat_medicalunit
WHERE key_issste IS NOT NULL AND clues_id IS NULL
LIMIT 200
"""


def text_normalizer(text):
    import unidecode
    import re
    if not text:
        return ""
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^a-zA-Z0-9\s\-]', '', text)
    final_text = re.sub(r' +', ' ', text)
    return final_text.strip()


def clean_delegation_medical_unit(prov_id):
    from med_cat.models import MedicalUnit
    from geo.models import Delegation, CLUES
    umaes = [
        "Especialidades Coahuila",
        "Especialidades Guanajuato",
        "Especialidades Jalisco",
        "Especialidades La Raza",
        "Especialidades Nuevo Leon",
        "Especialidades Puebla",
        "Especialidades Sonora",
        "Especialidades SXXI",
        "Especialidades Veracruz",
        "Especialidades Yucatan",
        "General La Raza",
        "Gineco Jalisco",
        "Gineco Nuevo Leon",
        "Gineco Pediatria Guanajuato",
        "Gineco SXXI",
        "Ginecologia La Raza",
        "Cardiologia Nuevo Leon",
        "Cardiologia SXXI",
        "Oncologia SXXI",
        "Pediatria Jalisco",
        "Pediatria SXXI",
        "Traumatologia Lomas Verdes",
        "Traumatologia Magdalena de las Salinas",
        "Traumatologia Nuevo Leon",
        "Traumatologia Puebla"
    ]
    umaes_delegation = Delegation.objects.get(name="TODAS LAS UMAES")
    delegation_dict = {}
    delegations = Delegation.objects.filter(provider_id=prov_id)
    base_units = MedicalUnit.objects.filter(
        provider_id=prov_id, delegation__isnull=True)
    for delegation in delegations:
        name = text_normalizer(delegation.name)
        delegation_dict[name] = delegation
        if delegation.other_names:
            for other_name in delegation.other_names:
                other_name = text_normalizer(other_name)
                delegation_dict[other_name] = delegation
    all_medical_units = base_units.filter(delegation_name__isnull=False)
    unique_delegations = all_medical_units.values_list(
        "delegation_name", flat=True).distinct()
    for delegation in unique_delegations:
        delegation_name = text_normalizer(delegation)
        has_especialidades = "ESPECIALIDADES" in delegation_name
        has_umae = delegation_name.startswith("UMAE")
        if has_especialidades or has_umae or delegation in umaes:
            base_units.filter(
                delegation_name=delegation).update(
                delegation=umaes_delegation)
            continue
        delegation_name = delegation_name.replace("ALMACEN DELEGACIONAL EN ", "")
        delegation_name = text_normalizer(delegation_name)
        if delegation_name in delegation_dict:
            base_units.filter(
                delegation_name=delegation).update(
                delegation=delegation_dict[delegation_name])
        else:
            print("Delegation not found:", delegation_name)


# clean_delegation_medical_unit(55)

# EL DF ZONA SUR
#  ALMACEN SUBDELEGACIONAL EN TAPACHULA CHIAPAS
#  VERACRUZ PUERTO EXT BIENES TERAPEUTICOS
#  EL DF ZONA NORTE
#  EL ESTADO DE MEXICO PONIENTE
#  ESTADO DE MEXICO ORIENTE


def clean_clues_medical_unit(prov_id, update=False):
    from med_cat.models import MedicalUnit
    from geo.models import CLUES, Provider
    import re

    provider = Provider.objects.get(id=prov_id)
    clues = CLUES.objects.filter(institution_id=provider.institution_id)
    # base_units = MedicalUnit.objects.filter(
    #     provider_id=prov_id, clues__isnull=True, name__isnull=False)
    base_units = MedicalUnit.objects.filter(
        provider_id=prov_id, clues__isnull=True, name__isnull=False,
        own_key__isnull=False)
    init_remain = ["Direccion", "Farmacia"]
    clues_dict = {}
    for clue in clues:
        std_name = f"{clue.prev_clasif_name} {clue.number_unity} - {clue.state_id}"
        std_name = text_normalizer(std_name)
        clues_dict[std_name] = clue
    ready_names = set()
    success_count = 0
    close_count = 0
    total_print = 0
    unique_clasif = set()
    for unit in base_units:
        name = unit.name
        if name in ready_names:
            continue
        ready_names.add(name)
        for init in init_remain:
            if name.startswith(init):
                name = name.replace(init, "")
        # get the first characters before the first number
        only_name = re.sub(r'\d+', '', name)
        # get the first numbers together
        arr_nums = re.findall(r'\d+', name)
        first_num = ""
        if arr_nums:
            first_num = arr_nums[0]
        if not first_num:
            continue
        if not unit.delegation:
            continue

        state_id = unit.delegation.state_id
        built_name1 = f"{only_name} {first_num} - {state_id}"
        built_name1 = text_normalizer(built_name1)
        first_name = built_name1.split(" ")[0]
        built_name2 = f"{first_name} {first_num} - {state_id}"
        built_name2 = text_normalizer(built_name2)
        unique_clasif.add(first_name)
        is_success = False
        for built_name in [built_name1, built_name2]:
            if built_name in clues_dict:
                if update:
                    base_units.filter(name=unit).update(
                        clues=clues_dict[built_name])
                success_count += 1
                is_success = True
                break

        if not is_success and total_print < 20:
            print("unit_name", unit.name)
            print("built_name1", built_name1)
            print("built_name2", built_name2)
            print("-" * 20)
            total_print += 1
            close_count += 1
        elif not is_success:
            close_count += 1
    print()
    print("close_count", close_count)
    print("total_names", len(ready_names))
    print("success_count", success_count)
    print("unique_clasif", unique_clasif)


clean_clues_medical_unit(55, update=False)
