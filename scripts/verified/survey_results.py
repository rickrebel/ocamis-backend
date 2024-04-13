from intl_medicine.models import PrioritizedComponent
from medicine.models import Group
from scripts.csv_export.generic import CsvExporter
from django.db.models import Count, Q


def get_prioritized_components():
    # count the total number of responses and if is_prioritized or not
    data = {}
    components = {}
    query_init = PrioritizedComponent.objects.filter(
        group_answer__respondent__isnull=True,
    ).distinct()

    def build_name(p_comp):
        group_obj = p_comp.group_answer.group
        group_name = f"{group_obj.number}. {group_obj.name}"
        return p_comp.component.name, f"{p_comp.component.name}|{group_name}"

    for pc in query_init:
        final_name, name = build_name(pc)
        data[final_name] = {
            "prioritized": pc.is_prioritized,
            "priority": "low" if pc.is_low_priority else "high",
            "included": 0,
            "excluded": 0,
        }
        components.setdefault(name, {"included": 0, "excluded": 0})

    query = PrioritizedComponent.objects.filter(
        group_answer__is_valid=True,
        group_answer__respondent__isnull=False,
        is_prioritized__isnull=False
    ).distinct()

    for pc in query:
        final_name, name = build_name(pc)
        if final_name not in data:
            data[final_name] = {
                "prioritized": "XXXXX",
                "priority": "XXXXX",
                "included": 0,
                "excluded": 0,
            }
        if pc.is_prioritized:
            data[final_name]["included"] += 1
            components[name]["included"] += 1
        else:
            data[final_name]["excluded"] += 1
            components[name]["excluded"] += 1
    query_data = []

    for final_name, pc in data.items():
        component, group = final_name.split("|")
        component = component.strip()
        group = group.strip()
        included = pc["included"]
        excluded = pc["excluded"]
        total = included + excluded
        all_included = components.get(component, {}).get("included", 0)
        all_excluded = components.get(component, {}).get("excluded", 0)

        query_data += [
            [group, component, pc["prioritized"], pc["priority"], included,
             excluded, total, all_included, all_excluded]
        ]

    csv_ex = CsvExporter(
        query=query_data,
        headers=[
            "Grupo Terapeútico (name)",
            "# Componente (name)",
            "Priorizado inicialmente (bool)",
            "Prioridad",
            "# de incluídos",
            "# de excluídos",
            "Total de respuestas",
            "Incluidas mismo nombre",
            "Excluidas mismo nombre",
        ],
        attributes=None,
        file_path="fixture/survey/Priorizado.csv",
    )

    csv_ex.generate_csv()

    # Como se calcula el # de incluídos y excluídos?

    # query = Group.objects.annotate(
    #     valid_responses_count=Count(
    #         'responses',
    #         filter=Q(responses__is_valid=True) & ~Q(responses__respondent=None)
    #     )
    # )
    #
    # csv_ex2 = CsvExporter(
    #     query=[
    #         [group.name, group.valid_responses_count]
    #         for group in query
    #     ],
    #     headers=[
    #         "Grupo terapeútico (name)",
    #         "número de ejercicios efectivos",
    #     ],
    #     attributes=None,
    #     file_path="Grupos_terapeuticos.csv",
    # )
    #
    # csv_ex2.generate_csv()
