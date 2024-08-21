def get_medicament_fields():
    from med_cat.models import Medicament
    all_fields = Medicament._meta.get_fields(
        include_parents=False, include_hidden=False)
    final_fields = []
    for field in all_fields:
        if field.one_to_many:
            continue
        complement = "_id" if field.is_relation else ""
        field_name = f"{field.name}{complement}"
        final_fields.append(field_name)
    return final_fields


def update_med_container_simple(update=True):
    from med_cat.models import Medicament
    from medicine.models import Container
    print_count = 0
    # medicaments_with_key2 = Medicament.objects.filter(
    #     key2__isnull=False, own_key2__isnull=True, container__isnull=True)
    medicaments_with_key2 = Medicament.objects.filter(
        key2__isnull=False, container__isnull=True)
    print("medicaments_remains", medicaments_with_key2.count())
    medicaments_ready = Medicament.objects.filter(
        key2__isnull=False, container__isnull=False)
    print("medicaments_ready", medicaments_ready.count())
    all_fields = get_medicament_fields()
    remains = {"010": [], "others": []}
    if not update:
        return remains
    for medicament in medicaments_with_key2:
        key2 = medicament.key2
        container_found = Container.objects.filter(key2=key2).first()
        if not container_found and len(key2) == 13:
            new_key2 = medicament.key2[:-2]
            new_key2 = f"0{new_key2}"
            container_found = Container.objects\
                .filter(key2=new_key2).first()
        if not container_found and len(key2) == 14:
            new_key2 = medicament.key2[:-2]
            container_found = Container.objects\
                .filter(key2=new_key2).first()
        if container_found:
            medicament.container = container_found
            medicament.save()
        else:
            if key2[:3] != "010":
                remains["others"].append(medicament)
                continue
            else:
                remains["010"].append(medicament)
                if print_count > 10:
                    continue
                print("container not found", key2)
                for field in all_fields:
                    print(field, getattr(medicament, field))
                print_count += 1
                print("--------------------")
    return remains


# rems = update_med_container_simple()
# Elimina los últimos caracteres e intenta buscar los contenedores sin
# revisar cuáles caracteres son. Además, intenta filtrar duplicados
def update_med_container_id():
    from med_cat.models import Medicament
    from medicine.models import Container
    from geo.models import Provider
    prints_count = 0
    provider_imss = Provider.objects.get(id=55)
    all_fields = get_medicament_fields()
    medicaments_own_imss = Medicament.objects.filter(
        provider=provider_imss)
    errors = {
        "Key no encontrada": [], "No tiene formato correcto": [],
        "Multiples contenedores": [], "Otros errores": []}
    success_count = 0
    for medicament in medicaments_own_imss:
        medi_own_key2 = medicament.own_key2[:-2]
        container_found = Container.objects\
            .filter(key2=medi_own_key2).first()
        if not container_found:
            new_medi_own_key2 = f"0{medi_own_key2}"
            container_found = Container.objects\
                .filter(key2=new_medi_own_key2).first()
        if container_found:
            medicament.container = container_found
            medicament.save()
        else:
            errors["Key no encontrada"].append(medicament.own_key2)
    return success_count, errors


def reporte_med_container():
    successes_medicament, errors_medicament = update_med_container_id()
    print("Casos exitosos:", successes_medicament)
    error_count = 0
    for key, values in errors_medicament.items():
        error_count += len(values)
        # print(key, len(values))
    print("Conteo total de errores:", error_count)
    return errors_medicament


# final_errors = reporte_med_container()
