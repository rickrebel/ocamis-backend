from scripts.ocamis_verified.catalogs.scrapper.start import Scrapper
from scripts.ocamis_verified.catalogs.compendio2 import special_normalizer
import json


scrapper = Scrapper()


error_complements = [
    "/cnis/010.000.6239.00/3/Labetalol?cc=mx",
    "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino?cc=mx",
    "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino besilato/indapamida?cc=mx",
    "/cnis/010.000.7077.00/4/Risankizumab?cc=mx",
    "/cnis/010.000.7078.00/5/Dapagliflozina propanodiol?cc=mx",
    "/cnis/010.000.7078.00/5/Semaglutida?cc=mx",
    "/cnis/010.000.7073.00/8/Diosmina/hesperidina?cc=mx",
    "/cnis/010.000.7069.00/10/Carboximaltosa\nférrica?cc=mx",
    "/cnis/010.000.7069.00/10/Isatuximab?cc=mx",
    "/cnis/010.000.4340.00/13/Omalizumab?cc=mx",
    "/cnis/010.000.7075.00/14/Fampridina?cc=mx",
    "/cnis/010.000.6302.00/16/Darolutamida?cc=mx",
    "/cnis/010.000.5610.01/16/Lanreótida acetato?cc=mx",
    "/cnis/010.000.6302.00/16/Ponatinib?cc=mx",
    "/cnis/040.000.3215.00/19/Diazepam?cc=mx",
    "/cnis/010.000.4512.01/20/Adalimumab?cc=mx",
    "/cnis/010.000.7074.00/20/Upadacitinib?cc=mx"]


# scrapper.explore_group(1)
# print("current_group:", scrapper.current_group)
# scrapper.explore_component("/cnis/010.000.0247.01/1/Dexmedetomidina clorhidrato?cc=mx")
# print("component:", scrapper.all_components)

print("all_components:", len(scrapper.all_components))
for component in scrapper.all_components:
    if component["group_name"] != component["parent_group"]:
        # print("key:", key)
        print("component:", component["name"])
        print(component["group_name"], "<>", component["parent_group"])
        print()
        continue


scrapper.build_all_keys()
# print("all_keys:", len(scrapper.all_keys))
group_names = set()
for component in scrapper.all_components:
    group_names.add(component["group_name"])

print("group_names:", group_names)


def count_errors(field=None, component_field=None):
    erros_count = 0
    for key, values in scrapper.all_keys.items():
        unique_values = set()
        if field:
            unique_values = {v[field] for v in values}
        elif component_field:
            unique_values = {v["component"][component_field] for v in values}
        if len(unique_values) > 1:
            erros_count += 1
            if erros_count < 20:
                print("key:", key)
                print(field, ":", unique_values)
                print("-" * 20)
    print("error_count:", erros_count)


def some_tests():
    count_errors("presentation_name")
    count_errors("presentation_description")
    count_errors("container_description")
    count_errors(component_field="name")


def save_all_groups():
    for group_id in range(1, 23):
        print("group_id:", group_id)
        try:
            scrapper.explore_group(group_id)
            scrapper.explore_components()
            scrapper.save_json()
        except Exception as e:
            print("error en group_id:", group_id)
            print("e:", e)

    scrapper.save_json()


def build_all_groups():
    for group_id in range(1, 23):
        print("group_id:", group_id)
        try:
            scrapper.explore_group(group_id)
        except Exception as e:
            print("error en group_id:", group_id)
            print("e:", e)


def special_assign():
    real_idx = -1
    total_errors = 0
    continuos_errors = 0
    last_pairs = None
    for (idx, parent_component) in enumerate(scrapper.component_list):
        if parent_component["url"] in error_complements:
            continue
        real_idx += 1
        saved_component = scrapper.all_components[real_idx]
        saved_name = special_normalizer(saved_component["name"])
        parent_name = special_normalizer(parent_component["name"])
        # same_name = saved_name == parent_name
        scrapper.all_components[real_idx]["parent_name"] = parent_name
        scrapper.all_components[real_idx]["url"] = parent_component["url"]

    scrapper.save_json()




