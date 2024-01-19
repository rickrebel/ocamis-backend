from scripts.ocamis_verified.catalogs.compendio import ProcessPDF
from scripts.ocamis_verified.catalogs.standard import (
    calculate_standard, some_is_standard)
from medicine import models
from scripts.common import text_normalizer


def special_normalizer(text):
    text = text.replace("/", " ")
    text = text_normalizer(text)
    return text.strip()


file_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/compendio_2023.pdf"
process = ProcessPDF(file_path)
process(800)
# process(pages_range=(79, 350))


all_containers = []
for comp in process.all_components:
    for presentation in comp['presentations']:
        for container in presentation['keys']:
            all_containers.append(container)

not_standard = []
for container in all_containers:
    description = container['description']
    if not calculate_standard(description):
        not_standard.append(container)

for container in all_containers:
    print(container['key'])

print("len_not_standard", len(not_standard))

for container in not_standard:
    print(container['key'], container['description'])


all_components_objs = {}
for comp in models.Component.objects.all():
    name = special_normalizer(comp.name)
    all_components_objs[name] = comp

for comp in process.all_components:
    comp_name = special_normalizer(comp['name'])
    if comp_name not in all_components_objs:
        print(comp_name)
        continue


pdf_components = {}
for comp in process.all_components:
    comp_name = special_normalizer(comp['name'])
    pdf_components[comp_name] = comp


all_containers_objs = {}

for container in models.Container.objects.all():
    all_containers_objs[container.key] = container

for container in all_containers:
    key = container['key']
    if key not in all_containers_objs:
        print(key)
        continue

pdf_containers = {}
for container in all_containers:
    key = container['key']
    pdf_containers[key] = container

remain_components = set()
for container in models.Container.objects.all():
    key = container.key
    if key:
        component = container.presentation.component.name
        normal_component = special_normalizer(component)
        if key not in pdf_containers and normal_component not in pdf_components:
            remain_components.add(normal_component)
            print(key, normal_component)
            continue

for comp in remain_components:
    print(comp)



# HIALURONATO DE SODIO (384)
# GOTAS LUBRICANTES OCULARES
# SISTEMA INTEGRAL PARA LA APLICACIÓN DE DIÁLISIS PERITONEAL AUTOMATIZADA
# LITIO
# BELIMUMAB
# FACTOR X DE COAGULACIÓN HUMANO








