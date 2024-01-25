from scripts.ocamis_verified.catalogs.scrapper.start import Scrapper


scrapper = Scrapper()

# scrapper.explore_group(1)
# print("current_group:", scrapper.current_group)
# scrapper.explore_component("/cnis/010.000.0247.01/1/Dexmedetomidina clorhidrato?cc=mx")
# print("component:", scrapper.all_components)

scrapper.build_all_keys()
print("all_keys:", len(scrapper.all_keys))


def save_all_groups():
    for group_id in range(2, 23):
        print("group_id:", group_id)
        try:
            scrapper.explore_group(group_id)
            scrapper.explore_components()
            scrapper.save_json()
        except Exception as e:
            print("error en group_id:", group_id)
            print("e:", e)

    scrapper.save_json()


error_complements = [
    "/cnis/010.000.6239.00/3/Labetalol?cc=mx",
    "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino?cc=mx",
    "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino besilato/indapamida?cc=mx",
    "/cnis/010.000.7077.00/4/Risankizumab?cc=mx",
    "/cnis/010.000.7078.00/5/Dapagliflozina propanodiol?cc=mx",
    "/cnis/010.000.7078.00/5/Semaglutida?cc=mx",
    "/cnis/010.000.7073.00/8/Diosmina/hesperidina?cc=mx",
    "/cnis/010.000.7069.00/10/Carboximaltosa férrica?cc=mx",
    "/cnis/010.000.7069.00/10/Isatuximab?cc=mx",
    "/cnis/010.000.4340.00/13/Omalizumab?cc=mx",
    "/cnis/010.000.7075.00/14/Fampridina?cc=mx",
    "/cnis/010.000.6302.00/16/Darolutamida?cc=mx",
    "/cnis/010.000.5610.01/16/Lanreótida acetato?cc=mx",
    "/cnis/010.000.6302.00/16/Ponatinib?cc=mx",
    "/cnis/040.000.3215.00/19/Diazepam?cc=mx",
    "/cnis/010.000.4512.01/20/Adalimumab?cc=mx",
    "/cnis/010.000.7074.00/20/Upadacitinib?cc=mx"]





