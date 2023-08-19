# def update_medicament_entity_id():
#     from med_cat.models import Medicament
#     from geo.models import Entity
#     # medicaments_own_imss = Medicament.objects.filter(
#     #     key2=55, own_key2__isnull=False)
#     # medicaments_own_imss.update(entity=55)
#     medicaments_own_imss = Medicament.objects.filter(
#         key2__isnull=False, own_key2__isnull=False)
#     for medicament in medicaments_own_imss:
#         key2_to_move = medicament.key2
#         entity_obj = Entity.objects.get(id=key2_to_move)
#         medicament.entity = entity_obj
#         medicament.key2 = None
#         medicament.save()


def update_medicament_entity_id():
    from med_cat.models import Medicament
    from geo.models import Entity
    # medicaments_own_imss = Medicament.objects.filter(
    #     key2=55, own_key2__isnull=False)
    # medicaments_own_imss.update(entity=55)
    medicaments_own_imss = Medicament.objects.filter(
        key2__isnull=False, own_key2__isnull=False)
    for medicament in medicaments_own_imss[:15]:
        key2_to_move = medicament.key2
        entity_obj = Entity.objects.get(id=key2_to_move)
        medicament.entity = entity_obj
        medicament.key2 = None
        # medicament.save()


# update_medicament_entity_id()
