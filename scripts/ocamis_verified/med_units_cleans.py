
def update_delegation_in_med_units(entity_id):
    from med_cat.models import MedicalUnit
    from geo.models import Delegation, Entity
    from scripts.common import text_normalizer
    from geo.views import build_catalog_delegation_by_id
    entity = Entity.objects.get(id=entity_id)
    dict_delegations = build_catalog_delegation_by_id(entity.institution)
    all_medical_units = MedicalUnit.objects.filter(
        entity=entity, delegation__isnull=True, delegation_name__isnull=True)
    print("all_medical_units", all_medical_units.count())
    for medical_unit in all_medical_units:
        delegation_name = text_normalizer(medical_unit.delegation_name)
        if delegation_name in dict_delegations:
            try:
                delegation_id = dict_delegations[delegation_name]
                delegation_found = Delegation.objects.get(id=delegation_id)
                if delegation_found.is_clues:
                    medical_unit.clues = delegation_found.all_clues.first()
                if "UMAE " in delegation_name:
                    delegation_id = dict_delegations["TODAS LAS UMAES"]
                # medical_unit.delegation_id = delegation_id
                # medical_unit.save()
            except Exception as e:
                print("error", e)
                print("delegation_name", delegation_name)
        else:
            print("medical_unit", medical_unit)
            print("delegation not found", delegation_name)


# update_delegation_in_med_units(55)


def update_clues():
    from med_cat.models import MedicalUnit
    from geo.models import CLUES

    med_units = MedicalUnit.objects.filter(
        clues__isnull=True)
    fields = [["clues", "clues_key"], ["key_issste", "key_issste"]]
    units = {}

    # units["with_clues"] = med_units.filter(clues_key__isnull=False)
    # units["with_issste"] = med_units.filter(key_issste__isnull=False)

    success_counts = {}
    errors = {}

    succes_count = 0

    # for name_coll, med_units in units.items():
    for field_in_unit, field_in_clues in fields:
        errors[field_in_clues] = {
            "CLUES no encontrada": [], "Multiples CLUES": [],
            "Otros errores": [] }

        success_counts[field_in_clues] = 0
        # field_to_filter = "clues" if name_coll == "with_clues" \
        #     else "key_issste"
        fields_in_unit_isnull = f"{field_in_unit}__isnull"  # clues__isnull , key_issste__isnull
        current_med_units = med_units.filter(**{fields_in_unit_isnull: False})
        for unit in current_med_units:

            elem_value = getattr(unit, field_in_clues)
            # unit_clues = unit.clues_key
            # unit_key_issste = unit.key_issste

            try:
                query_get = {
                    field_in_clues: elem_value
                }
                value_to_assign = CLUES.objects.get(**query_get)

                # ESTÁ MAAAL
                # clues_to_assign = CLUES.objects.get(
                #     clues=unit_clues, key_issste=unit_key_issste)

                # EJEMPLO DE EQUIVALENCIA
                # clues_to_assign = CLUES.objects.get(clues=unit_clues)
                # clues_to_assign = CLUES.objects.get(**{"clues": unit_clues})
                unit.clues = value_to_assign
                success_counts[field_in_clues] += 1
                succes_count += 1
                # unit.save()
            except CLUES.DoesNotExist:
                errors[field_in_clues]["CLUES no encontrada"].append(unit)
            except CLUES.MultipleObjectsReturned:
                # No tendría que llegar a este caso
                errors[field_in_clues]["Multiples CLUES"].append(unit)
            except Exception as e:
                errors[field_in_clues]["Otros errores"].append(unit)

    return success_counts, errors


# update_clues(53, "key_issste")
# variables = [53, "key_issste"]
# update_clues(*variables)


def reporte_clues():
    successes_clues, errors_clues = update_clues()
    print("Casos exitosos:", successes_clues)
    error_count = 0
    for field, field_errors in errors_clues.items():
        for type_error, values in field_errors.items():
            error_count += len(values)
            print(type_error, len(values))
    print("Conteo total de errores:", error_count)
    return errors_clues


# errors = reporte_clues()

