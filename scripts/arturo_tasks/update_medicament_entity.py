# def update_medicament_entity_id():
#     from med_cat.models import Medicament
#     from geo.models import Provider
#     # medicaments_own_imss = Medicament.objects.filter(
#     #     key2=55, own_key2__isnull=False)
#     # medicaments_own_imss.update(entity=55)
#     medicaments_own_imss = Medicament.objects.filter(
#         key2__isnull=False, own_key2__isnull=False)
#     for medicament in medicaments_own_imss:
#         key2_to_move = medicament.key2
#         entity_obj = Provider.objects.get(id=key2_to_move)
#         medicament.entity = entity_obj
#         medicament.key2 = None
#         medicament.save()


def update_medicament_entity_id():
    from med_cat.models import Medicament
    from geo.models import Provider
    medicaments_own_imss = Medicament.objects.filter(
        key2__isnull=False, own_key2__isnull=False)
    success_count = 0
    for medicament in medicaments_own_imss:
        key2_to_move = medicament.key2
        try:
            entity_obj = Provider.objects.get(id=key2_to_move)
            medicament.entity = entity_obj
            medicament.key2 = None
            medicament.save()
            success_count += 1
        except Exception as e:
            print("e", e)
            continue
    print("success_count", success_count)


update_medicament_entity_id()
