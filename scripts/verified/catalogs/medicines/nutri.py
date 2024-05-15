
from scripts.verified.catalogs.medicines.compendio import ProcessPDF
from scripts.verified.catalogs.medicines.compendio2 import (
    nutri_files, special_normalizer)
from intl_medicine.models import GroupAnswer, PrioritizedComponent
from medicine.models import Component, Group


def get_pdf_nutrition():
    process = ProcessPDF(
        nutri_files["pdf"], json_path=nutri_files["json"], is_nutrition=True)
    process(150)
    process.save_json()


class ProcessNutri:
    def __init__(self):
        self.json_path = nutri_files["json"]
        self.pdf_path = nutri_files["pdf"]
        # self.process = ProcessPDF(self.pdf_path, is_nutrition=True)
        self.nutri_pdf = None
        nutri_group = Group.objects.filter(name="Nutriología").first()
        self.nutri_ga, _ = GroupAnswer.objects.get_or_create(
            respondent=None, group=nutri_group)

    def process_pdf(self):
        self.nutri_pdf = ProcessPDF(nutri_files["pdf"], is_nutrition=True)
        # nutri_pdf(pages_range=[1, 2])
        # nutri_pdf(pages_range=[1, 10])
        # nutri_pdf.first_page
        self.nutri_pdf(150)

    def add_pc(self, component):
        print("component_name:", component.name)
        PrioritizedComponent.objects.get_or_create(
            component=component, group_answer=self.nutri_ga)

    def create_component(self, comp_name):
        print("----new:", comp_name)
        component = Component.objects\
            .filter(name=comp_name)\
            .order_by("containers_count", "id").first()
        if not component:
            component = Component(name=comp_name)
            component.save()
        self.add_pc(component)

    def __call__(self):
        # comp_names = self.nutri_pdf.component_names
        # print("comps:", len(comp_names))
        # print("unique comps:", len(set(comp_names)))

        saved_components = Component.objects.filter(
            groups_pc_count=0, containers_count__gt=0)
        saved_comps = {special_normalizer(comp.name, True): comp
                       for comp in saved_components}

        orphan_comps = {}
        all_components = []
        sorted_comps = sorted(self.nutri_pdf.component_names)

        for component_name in sorted_comps:
            normalized = special_normalizer(component_name, True)
            comp = {"name": component_name, "normalized": normalized}
            all_components.append(comp)
            orphan_comps[normalized] = comp

        unique_names = set(saved_comps.keys() | orphan_comps.keys())
        sorted_unique = sorted(unique_names)
        # print("-----------------")

        not_found = []
        for name in sorted_unique:
            saved = saved_comps.get(name)
            pdf = orphan_comps.get(name)
            if not pdf or not saved:
                if not pdf:
                    if "VITAMINAS A C Y D" in saved.name:
                        self.add_pc(saved)
                    elif "LÍPIDOS/AMINOÁCIDOS/GLUCOSA" in saved.name:
                        self.add_pc(saved)
                    else:
                        not_found.append(saved.name)
                elif "LÍPIDOS/AMINOÁCIDOS/GLUCOSA" in pdf["name"]:
                    print(f"saved not found:", pdf["name"])
                else:
                    self.create_component(pdf["name"])
            else:
                self.add_pc(saved)

        for name in not_found:
            print("not found pdf:", name)
