def groups_assignation():
    from medicine.models import Container, Presentation

    all_containers = Container.objects.all()
    all_presentations = Presentation.objects.filter(group__isnull=False)

    for presentation in all_presentations:
        presentation.groups.add(presentation.group)

    # for container in all_containers: