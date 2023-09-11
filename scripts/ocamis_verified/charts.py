from django.db.models import Count, F, Sum
from formula.models import Drug, MotherDrugPriority
import matplotlib.pyplot as plt
import numpy as np


def get_data(entity_id=55, component_id=96, **kwargs):
    from geo.models import Delegation, CLUES, Entity
    from medicine.models import Component
    title = "Evolución "
    query_filter = {}
    if component_id:
        component = Component.objects.get(id=component_id)
        title += f"de {component.name}"
        query_filter['container__presentation__component_id'] = component_id
    if kwargs.get('clues_id'):
        clues_id = kwargs.get('clues_id')
        clues = CLUES.objects.get(id=clues_id)
        title += f" en la unidad {clues.name}"
        query_filter['clues_id'] = clues_id
    elif kwargs.get('delegation_id'):
        delegation_id = kwargs.get('delegation_id')
        delegation = Delegation.objects.get(id=delegation_id)
        title += f" en la delegación {delegation.name}"
        query_filter['delegation_id'] = delegation_id
    elif entity_id:
        entity = Entity.objects.get(id=entity_id)
        title += f" del proveedor {entity.acronym}"
        query_filter['entity_week__entity_id'] = entity_id

    drugs = MotherDrugPriority.objects \
        .filter(**query_filter) \
        .exclude(delivered_id="cancelled") \
        .prefetch_related('entity_week') \
        .values('entity_week__iso_week', 'entity_week__iso_year') \
        .annotate(
            total=Sum('total'),
            delivered=Sum('delivered_total'),
            prescribed=Sum('prescribed_total'),
            iso_week=F('entity_week__iso_week'),
            iso_year=F('entity_week__iso_year'),
        ) \
        .values('iso_week', 'iso_year', 'total', 'delivered', 'prescribed') \
        .order_by('iso_year', 'iso_week')
    return drugs, title


def compute_spiral_coordinates(data):
    theta = []  # angle
    r = []  # radius
    r2 = []  # radius2
    heights = []  # bar heights
    heights2 = []  # bar heights
    base_radius = max([d["prescribed"] for d in data]) * 1.2
    min_year = min([d["iso_year"] for d in data])
    max_year = max([d["iso_year"] for d in data])

    for entry in data:
        week = entry["iso_week"]
        year = entry["iso_year"]
        delivered = entry["delivered"]
        not_delivered = entry["prescribed"] - entry["delivered"]

        # One circle for each year, 53 weeks in a circle
        sum_year = year - min_year
        rest_year = max_year - year
        angle = 2 * np.pi * week / 53.0
        theta.append(angle)

        radius = (sum_year + (week / 53.0)) * base_radius + base_radius
        r.append(radius)
        radius2 = radius + not_delivered
        r2.append(radius2)
        # cumulative_total += total
        # r.append(cumulative_total)

        # Bar width is proportional to total
        # widths.append(total)
        heights.append(not_delivered)
        heights2.append(delivered)

    # return theta, r, heights
    return theta, r, heights, r2, heights2


def plot_spiral_bar_chart(data, title):
    # theta, r, widths = compute_condegram_coordinates(data)
    theta, r, heights, r2, heights2 = compute_spiral_coordinates(data)
    # print(theta)
    ax = plt.subplot(111, projection='polar')
    ax2 = plt.subplot(111, projection='polar')

    bars = ax.bar(
        theta,
        heights,
        width=2 * np.pi / 53,
        bottom=r,
        color='#9b16de',
        edgecolor='black',
        linewidth=0.1
    )
    bars2 = ax2.bar(
        theta,
        heights2,
        width=2 * np.pi / 53,
        bottom=r2,
        edgecolor='black',
        linewidth=0.1
    )
    ax.set_theta_zero_location('N')  # Set 0° to the top of the plot
    ax.set_theta_direction(-1)  # Clockwise
    ax.get_yaxis().set_visible(False)  # Hide radial (y-axis) labels

    ax2.set_theta_zero_location('N')  # Set 0° to the top of the plot
    ax2.set_theta_direction(-1)  # Clockwise
    ax2.get_yaxis().set_visible(False)  # Hide radial (y-axis) labels
    for bar, height in zip(bars, heights):
        # bar.set_facecolor(plt.cm.turbo(1 - (height / max(heights))))
        bar.set_alpha(0.8)  # transparency
    for bar2, height in zip(bars2, heights2):
        bar2.set_facecolor(plt.cm.turbo(1 - (height / max(heights2))))
        bar2.set_alpha(0.8)  # transparency
    plt.title(title)
    plt.show(dpi=1500)


# # drug_data = get_data(53, 96, delegation_id=318)
# drug_data, title_chart = get_data(55, 208, delegation_id=320)
# plot_spiral_bar_chart(drug_data, title_chart)
#
# drug_data, title_chart = get_data(55, 208, delegation_id=254)
# plot_spiral_bar_chart(drug_data, title_chart)
#
# drug_data, title_chart = get_data(53, 208, delegation_id=281)
# plot_spiral_bar_chart(drug_data, title_chart)
#
# drug_data, title_chart = get_data(53, 208, delegation_id=283)
# plot_spiral_bar_chart(drug_data, title_chart)
#
#
# drug_data, title_chart = get_data(55, 96)
# plot_spiral_bar_chart(drug_data, title_chart)


