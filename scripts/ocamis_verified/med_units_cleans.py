
def update_delegation_in_med_units(entity_id):
    from med_cat.models import MedicalUnit
    from geo.models import Delegation, Entity
    from scripts.common import text_normalizer
    from geo.views import build_catalog_delegation_by_id
    entity = Entity.objects.get(id=entity_id)
    dict_delegations = build_catalog_delegation_by_id(entity.institution)
    all_medical_units = MedicalUnit.objects.filter(
        entity=entity, delegation__isnull=True, delegation_name__isnull=False)
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
        elif entity.acronym == "ISSSTE":
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
    med_units = MedicalUnit.objects.filter(
        clues__isnull=True)
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
