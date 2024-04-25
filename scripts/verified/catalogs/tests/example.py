
from scripts.verified.catalogs.compendio import ProcessPDF
from scripts.verified.catalogs.nutri import ProcessNutri
from scripts.verified.catalogs.compendio2 import (
    BuildNewTable, get_pdf_data, main_files, nutri_files, anonymize_responses,
    common_path)
from intl_medicine.models import GroupAnswer, Respondent


# get_pdf_data()

table = BuildNewTable(is_explore=False)
table()

table.analyze_components()
# table.analyze_groups()


# csv_groups_path = f"{common_path}/groups.csv"
# table.save_csv(csv_groups_path)
table.save_mini_csv()
table.save_csv()


pdf = ProcessPDF(main_files["pdf"])
pdf(pages_range=[671, 673])

print(pdf.first_page)


nutri = ProcessNutri()
nutri.process_pdf()
nutri()


def count_components():
    from medicine.models import Component
    for comp in Component.objects.all():
        comp.count()


def delete_new_components():
    from medicine.models import Component
    comps = Component.objects.filter(
        prioritizedcomponent__isnull=False,
        presentations__isnull=True)
    print("comps:", comps.distinct().count())
    comps.delete()


def propagate_prioritized(value=True, update=False):
    from medicine.models import Component
    from intl_medicine.models import PrioritizedComponent
    components = Component.objects.filter(
        prioritizedcomponent__is_prioritized=value,
        prioritizedcomponent__group_answer__respondent__isnull=True)
    print("components:", len(components))
    for component in components:
        pcs = PrioritizedComponent.objects.filter(
            component=component, group_answer__respondent__isnull=True)\
            .exclude(is_prioritized=value)
        if pcs.exists():
            print("component:", component.id, component.name)
            print("pcs:", pcs.count(), [pc.id for pc in pcs])
            if update:
                pcs.update(is_prioritized=value)


def identify_duplicates_names():
    from medicine.models import Component
    from django.db.models import Count, F
    components = Component.objects.values("name")\
        .annotate(count=Count("id")).filter(count__gt=1)
    for comp in components:
        print("comp:", comp["name"], comp["count"])
        # Component.objects.filter(name=comp["name"]).update(
        #     name=F("name") + " (duplicado)"


def propagate_low_priority(update=False):
    from medicine.models import Component
    from intl_medicine.models import PrioritizedComponent, Respondent
    original_resp = Respondent.objects.get(email="original@original.com")
    components = Component.objects.filter(
        prioritizedcomponent__is_prioritized=False,
        prioritizedcomponent__is_low_priority=True,
        prioritizedcomponent__group_answer__respondent=original_resp)
    print("components:", len(components))
    for component in components:
        pcs = PrioritizedComponent.objects.filter(
            component=component, group_answer__respondent__isnull=True)\
            .exclude(is_prioritized=True)
        if pcs.exists():
            print("component:", component.id, component.name)
            print("pcs:", pcs.count(), [pc.id for pc in pcs])
            if update:
                pcs.update(is_low_priority=True)


# 010.000.6282.00

# 040.000.2500.00
# 010.000.6276.00
# 010.000.6251.00


# VACUNA TRIPLE VIRAL (SRP ) CONTRA SARAMPIÓN, RUBÉOLA Y PAROTIDITIS

def null_to_false():
    from intl_medicine.models import PrioritizedComponent
    PrioritizedComponent.objects\
        .filter(is_low_priority__isnull=True)\
        .update(is_low_priority=False)
    PrioritizedComponent.objects\
        .filter(is_prioritized__isnull=True)\
        .update(is_prioritized=False)

