from scripts.ocamis_verified.catalogs.compendio import ProcessPDF
from scripts.ocamis_verified.catalogs.standard import (
    calculate_standard, some_is_standard)
from medicine import models
from scripts.common import text_normalizer
import json
import io
import csv


common_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/"

# json_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/compendio_2023.json"
file_path = f"{common_path}compendio_2023.pdf"
json_path = f"{common_path}compendio_2023.json"
csv_path = f"{common_path}compare_components.csv"


def delete_parenthesis(text):
    import re
    text = re.sub(r"\(.*?\)", "", text)
    return text


def special_normalizer(text):
    # delete all inside parenthesis:
    text = delete_parenthesis(text)
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text_normalizer(text)
    text = text.replace("METFORMINA LINAGLIPTINA", "LINAGLIPTINA METFORMINA")
    text = text.replace("LEVOTIROXINA SODICA", "LEVOTIROXINA")
    return text.strip()


def get_pdf_data():
    process = ProcessPDF(file_path)
    process(800)
    # process(pages_range=(79, 350))

    # save json in a file:
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(process.all_components, file, indent=4)


def move_components():
    from report.models import Supply
    from medicine.models import Presentation, Component
    from intl_medicine.models import PrioritizedComponent
    comps = [
        ('AMINOACIDOS CRISTALINOS', 'AMINOÁCIDOS CRISTALINOS'),
        ('AMOXICILINA-ACIDO CLAVULANICO', 'AMOXICILINA/ÁCIDO CLAVULÁNICO'),
        ('BROMURO DE TIOTROPIO'),
        ('BUSULFAN', 'BUSULFÁN'),
        ('IRBESARTAN, AMLODIPINO', 'IRBESARTÁN/AMLODIPINO'),
        ('IRBESARTAN-HIDROCLOROTIAZIDA', 'IRBESARTÁN/HIDROCLOROTIAZIDA'),
        ('LIDOCAINA', 'LIDOCAÍNA'),
    ]
    for comp in comps:
        bad_comp = Component.objects.filter(name=comp[0]).first()
        good_comp = Component.objects.filter(name=comp[1]).first()
        if bad_comp and good_comp:
            all_names = {bad_comp.name, good_comp.name, bad_comp.short_name,
                         good_comp.short_name}
            all_names = [n.strip() for n in all_names if n]
            if len(all_names) > 1:
                good_comp.alternative_names = list(all_names)
                good_comp.save()
            Presentation.objects.filter(component=bad_comp) \
                .update(component=good_comp)
            Supply.objects.filter(component=bad_comp) \
                .update(component=good_comp)
            PrioritizedComponent.objects.filter(component=bad_comp).delete()
            bad_comp.name = 'BORRADO'
            bad_comp.short_name = None
            bad_comp.group = None
            bad_comp.save()
        else:
            print("ERROR", comp)


def small_cleans():
    move_components()
    cleans = [
        ("BUSULFANO", "BUSULFAN"),
        ("LEUPROLIDA", "LEUPRORELINA"),
        # ("LEVOTIROXINA SODICA", "LEVOTIROXINA"),
        ("TIOTROPIO BROMURO", "BROMURO DE TIOTROPIO")
    ]
    for clean in cleans:
        models.Component.objects.filter(name=clean[0]).update(name=clean[1])
    asparta = models.Component.objects.filter(
        name__contains="ASPARTA SOLUBLE").first()
    if asparta:
        asparta.alternative_names = [asparta.name]
        asparta.name = "INSULINA ASPARTA"
        asparta.save()


class BuildNewTable:

    def __init__(self):
        # read json from a file (json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            self.all_components = json.load(file)
            print("len(all_components)", len(self.all_components))
        self.pdf_components = {}
        self.pdf_containers = {}
        self.saved_containers = {}
        self.saved_components = {}
        self.csv = io.StringIO()
        self.buffer = csv.writer(self.csv, delimiter="|")
        self.unique_components = set()
        self.ready_components = set()
        self.last_symbol = None
        self.current_comp_name = None
        self.warnings = {"many": [], "no": []}

    def __call__(self):
        small_cleans()
        self.build_first_objects()
        self.analyze_components()
        # self.save_csv()

    def build_first_objects(self):
        # 010.000.0101.00
        for comp in self.all_components:
            comp_name = special_normalizer(comp['name'])
            self.unique_components.add(comp_name)
            self.pdf_components.setdefault(comp_name, [])
            self.pdf_components[comp_name].append(comp)
            for presentation in comp['presentations']:
                presentation["component"] = comp
                for container in presentation['keys']:
                    container["presentation"] = presentation
                    key = container['key']
                    id_key = key[4:]
                    self.pdf_containers.setdefault(id_key, [])
                    self.pdf_containers[id_key].append(container)

        components_saved = models.Component.objects\
            .filter(presentations__containers__key__isnull=False)\
            .prefetch_related("presentations__containers")
        for comp in components_saved:
            name = special_normalizer(comp.name)
            self.unique_components.add(name)
            self.saved_components.setdefault(name, [])
            self.saved_components[name].append(comp)

        for container in models.Container.objects.all():
            key = container.key[4:]
            self.saved_containers[key] = container

    def analyze_components(self):
        ordered_components = sorted(list(self.unique_components))
        for comp_name in ordered_components:
            self.current_comp_name = comp_name
            if comp_name in self.ready_components:
                continue
            self.analyze_component(comp_name)

    def get_real_name(self, comp, source='pdf'):
        if not comp:
            return None, None
        if source == 'pdf':
            real_names = {delete_parenthesis(p['name']) for p in comp}
            elem_id = None
        else:
            real_names = {delete_parenthesis(p.name) for p in comp}
            ids = {p.id for p in comp}
            if len(ids) > 1:
                print("ERROR en MANY: saved; ids: ", ids, real_names)
                self.warnings['many'].append(f"{source}; {ids}")
                elem_id = "many"
            else:
                elem_id = ids.pop()
        cleaned_names = {special_normalizer(n) for n in real_names}
        if len(cleaned_names) > 1:
            print("ERROR en MANY: saved; names: ", real_names)
            self.warnings['many'].append(f"{source}; {real_names}")
        return real_names.pop(), elem_id

    def get_containers(self, component, source='pdf'):
        containers = []
        if not component:
            return containers
        for comp in component:
            if source == 'pdf':
                for pres in comp['presentations']:
                    for container in pres['keys']:
                        containers.append(container)
            elif source == 'saved':
                for container in comp.containers:
                    containers.append(container)
        return containers

    def analyze_component(self, comp_name):
        saved_comp = self.saved_components.get(comp_name)
        pdf_comp = self.pdf_components.get(comp_name)

        if not saved_comp and not pdf_comp:
            print("no saved_comp and no pdf_comp")
            return
        symbol = None
        comp_id = None

        if not pdf_comp:
            containers = self.get_containers(saved_comp, source='saved')
            for container in containers:
                key = container.key[4:]
                if pdf_container := self.pdf_containers.get(key):
                    # print("pdf_container", pdf_container)
                    new_comp_name = pdf_container[0]['presentation']['component']['name']
                    pdf_comp = self.get_component(
                        new_comp_name, source='pdf', key=key)
                    if pdf_comp:
                        # symbol = "⇼"
                        symbol = "<->"
                        break
        if not saved_comp:
            containers = self.get_containers(pdf_comp, source='pdf')
            for container in containers:
                key = container['key'][4:]
                if saved_container := self.saved_containers.get(key):
                    # print("saved_container", saved_container)
                    component = saved_container.presentation.component
                    saved_comp = self.get_component(
                        component.name, source='saved', key=key)
                    if saved_comp:
                        # symbol = "⇼"
                        symbol = "<->"
                        break

        real_name, _ = self.get_real_name(pdf_comp, source='pdf')
        saved_name, comp_id = self.get_real_name(saved_comp, source='saved')

        if not symbol:
            if not saved_name:
                # symbol = "≪"
                symbol = "<"
            elif not real_name:
                # symbol = "≫"
                symbol = ">"
            else:
                is_same = saved_name == real_name
                # symbol = "==" if is_same else "≅"
                symbol = "==" if is_same else "--"

        row = ['component', comp_id, 'name', saved_name, symbol, real_name]
        self.ready_components.add(comp_name)
        self.buffer.writerow(row)
        self.analyze_containers(saved_comp, pdf_comp)

    def write_container_row(self, pdf_cont, saved_cont, field):
        name = field['name']
        is_group = name == 'groups'
        is_pres = field.get('is_pres')
        pdf_value = None
        saved_value = None
        symbol = '?'
        fields = field.get('fields')
        elem_id = None
        if pdf_cont:
            if is_pres:
                values = []
                for cont in pdf_cont:
                    presentation = cont['presentation']
                    if is_group:
                        group = presentation['component']['group']
                        values.append(special_normalizer(group))
                    else:
                        value = presentation[fields[0]]
                        values.append(value)
                if is_group:
                    groups = sorted(values)
                    pdf_value = ", ".join(groups)
                else:
                    unique_values = set([special_normalizer(v) for v in values])
                    if len(unique_values) > 1:
                        self.warnings['many'].append(f"pdf; {values}")
                        print("\ndiff values", pdf_cont[0]['key'])
                        for value in values:
                            print(f"  {value}")
                    pdf_value = values[0]
            else:
                pdf_value = pdf_cont[0][fields[0]]
        if saved_cont:
            if is_pres:
                if is_group:
                    groups = saved_cont.presentation.groups.all()
                    text_groups = [special_normalizer(g.name) for g in groups]
                    text_groups = sorted(set(text_groups))
                    saved_value = ", ".join(text_groups)
                else:
                    saved_value = getattr(saved_cont.presentation, fields[1])
                    if name != 'text':
                        elem_id = saved_cont.presentation.id
            else:
                saved_value = getattr(saved_cont, fields[1])
                if name != 'text':
                    elem_id = saved_cont.id
        if pdf_value and saved_value:
            exact_same = pdf_value == saved_value
            if exact_same:
                symbol = "=="
            else:
                same_value = special_normalizer(pdf_value) == special_normalizer(saved_value)
                symbol = "--" if same_value else "!!"
        elif pdf_value:
            symbol = "<"
        elif saved_value:
            symbol = ">"
        row = [field['title'], elem_id, name, saved_value, symbol, pdf_value]
        self.buffer.writerow(row)

    def analyze_containers(self, saved_comp, pdf_comp):
        all_keys = set()

        pdf_containers = self.get_containers(pdf_comp, source='pdf')
        all_keys.update({c['key'][4:] for c in pdf_containers})
        saved_containers = self.get_containers(saved_comp, source='saved')
        all_keys.update({c.key[4:] for c in saved_containers})
        all_keys = sorted(list(all_keys))
        # fields = [
        #     {'row_names': ['  container', 'key'], 'fields': ('key', 'key')},
        #     {'row_names': ['  ', 'text'], 'fields': ('description', 'name')},
        #     {'row_names': ['  ', 'groups'], 'fields': ('description', 'name')},
        # ]
        fields = [
            {'title': '   container', 'name': 'key', 'fields': ('key', 'key')},
            {'title': '', 'name': 'text', 'fields': ('description', 'name')},
            {
                'title': '      present', 'name': 'name', 'is_pres': True,
                'fields': ('name', 'presentation_type_raw')},
            {
                'title': '', 'name': 'text', 'is_pres': True,
                'fields': ('description', 'description')},
            {'title': '', 'name': 'groups', 'is_pres': True},
        ]

        for short_key in all_keys:
            pdf_container = self.pdf_containers.get(short_key)
            saved_container = self.saved_containers.get(short_key)
            for field_data in fields:
                self.write_container_row(
                    pdf_container, saved_container, field_data)

    def get_component(self, comp_name, source='pdf', key=None):
        if source == 'pdf':
            origin = self.saved_components
            destination = self.pdf_components
        else:
            origin = self.pdf_components
            destination = self.saved_components
        comp_name = special_normalizer(comp_name)
        destination_comp = destination.get(comp_name)
        if destination_comp:
            origin_comp = origin.get(comp_name)
            if origin_comp:
                print(f"ERROR en MANY: {source}; key: {key}"
                      f"\n{comp_name} desde {self.current_comp_name}")
                return None
            if comp_name in self.ready_components:
                print(f"ERROR2 en READY: {source}; key: {key}"
                      f"\n{comp_name} desde {self.current_comp_name}")
            self.ready_components.add(comp_name)
            return destination_comp
        return None

    def save_csv(self, encoding="utf-8"):
        with open(csv_path, "w", encoding=encoding, newline="") as file:
            file.write(self.csv.getvalue())

    def analyze_groups(self):

        pdf_groups = set()
        for comp in self.all_components:
            group = comp['group']
            group = special_normalizer(group)
            if group:
                pdf_groups.add(group)

        saved_groups = models.Group.objects.all().values_list("name", flat=True)
        saved_groups = [special_normalizer(group) for group in saved_groups]

        for group in pdf_groups:
            if group not in saved_groups:
                print(group)

        for group in saved_groups:
            if group not in pdf_groups:
                print(group)


#########
#
# remain_components = set()
# for container in models.Container.objects.all():
#     key = container.key
#     if key:
#         component = container.presentation.component.name
#         normal_component = special_normalizer(component)
#         if key not in pdf_containers and normal_component not in pdf_components:
#             remain_components.add(normal_component)
#             print(key, normal_component)
#             continue
#
# for comp in remain_components:
#     print(comp)
#
# #########
#
# ########
#
# not_standard = []
# for container in pdf_containers:
#     description = container['description']
#     if not calculate_standard(description):
#         not_standard.append(container)
#
# for container in pdf_containers:
#     print(container['key'])
#
# print("len_not_standard", len(not_standard))
#
# for container in not_standard:
#     print(container['key'], container['description'])



# HIALURONATO DE SODIO (384)
# GOTAS LUBRICANTES OCULARES
# SISTEMA INTEGRAL PARA LA APLICACIÓN DE DIÁLISIS PERITONEAL AUTOMATIZADA
# LITIO
# BELIMUMAB
# FACTOR X DE COAGULACIÓN HUMANO
# EXENATIDA









