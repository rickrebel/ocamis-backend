
def groups_assignation():
    from django.db.models import Count
    from medicine.models import Presentation
    from med_cat.models import Medicament
    all_presentations = Presentation.objects.filter(group__isnull=False)
    # for presentation in all_presentations:
    #     presentation.groups.add(presentation.group)
    containers_with_duplicates = Presentation.objects\
        .values("containers__key2")\
        .annotate(group_count=Count('containers__key2'))\
        .filter(group_count__gt=1)
    for container in containers_with_duplicates:
        key2 = container["containers__key2"]
        presentations = Presentation.objects.filter(containers__key2=key2)
        first_presentation = presentations.first()
        duplicates_presentations = presentations.exclude(id=first_presentation.id)
        for dupli_presentation in duplicates_presentations:
            dupli_group = dupli_presentation.group
            if first_presentation.group != dupli_group:
                first_presentation.groups.add(dupli_group)
                print("supplies_count", Supply.objects.filter(
                    presentation=dupli_presentation).count())
                Supply.objects.filter(presentation=dupli_presentation)\
                    .update(presentation=first_presentation)
                dupli_containers = dupli_presentation.containers.all()
                for dupli_container in dupli_containers:
                    try:
                        first_container = first_presentation.containers\
                            .get(key2=dupli_container.key2)
                        print("first_container", first_container)
                        print("dupli_container", dupli_container)
                        print(Medicament.objects.filter(
                            container=dupli_container).count())
                        Medicament.objects.filter(container=dupli_container)\
                            .update(container=first_container)
                    except Exception as e:
                        print("e", e)
                        continue
                print("dupli_presentation", dupli_presentation)
                dupli_presentation.delete()


# groups_assignation()
