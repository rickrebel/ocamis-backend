
from scripts.ocamis_verified.catalogs.compendio import ProcessPDF
from scripts.ocamis_verified.catalogs.compendio2 import (
    BuildNewTable, get_pdf_data, main_files, nutri_files, get_pdf_nutrition,
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


nutri_pdf = ProcessPDF(nutri_files["pdf"], is_nutrition=True)
# nutri_pdf(pages_range=[1, 2])
# nutri_pdf(pages_range=[1, 10])
# nutri_pdf.first_page
nutri_pdf(150)
for component_name in nutri_pdf.component_names:
    print(component_name)


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


def anonymize_responses():
    original_resp = Respondent.objects.get_or_create(
        email="original@original.com", first_name="Original", last_name="Original",
        token="original", institution="Original", position="Original")[0]
    GroupAnswer.objects.filter(respondent=None).update(respondent=original_resp)
    GroupAnswer.objects\
        .filter(respondent__email="nuevo@nuevo.com")\
        .update(respondent=None)


# 010.000.6282.00

# 040.000.2500.00
# 010.000.6276.00
# 010.000.6251.00


# VACUNA TRIPLE VIRAL (SRP ) CONTRA SARAMPIÓN, RUBÉOLA Y PAROTIDITIS
