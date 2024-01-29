from scripts.ocamis_verified.catalogs.compendio import (
    ProcessPDF, is_every_upper)
from scripts.ocamis_verified.catalogs.scrapper.start import Scrapper
# from scripts.ocamis_verified.catalogs.standard import (
#     calculate_standard, some_is_standard)
import json
import io
import csv
from django.conf import settings
from medicine import models
from scripts.common import text_normalizer


is_local = settings.IS_LOCAL
base_dir = settings.BASE_DIR
if is_local:
    common_path = f"{base_dir}\\fixture\\medicines\\"
else:
    common_path = f"{base_dir}/fixture/medicines/"

# json_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/compendio_2023.json"
main_files = {
    "pdf": f"{common_path}compendio_2023.pdf",
    "json": f"{common_path}compendio_2023.json",
    "csv": f"{common_path}compare_components.csv",
}
nutri_files = {
    "pdf": f"{common_path}nutri_2023.pdf",
    "json": f"{common_path}nutri_2023.json",
    "csv": f"{common_path}compare_nutri.csv",
}
# file_path = f"{common_path}compendio_2023.pdf"
# nutri_path = f"{common_path}nutri_2023.pdf"
# json_path = f"{common_path}compendio_2023.json"
# json_nutri_path = f"{common_path}nutri_2023.json"
# csv_path = f"{common_path}compare_components.csv"


def delete_non_upper_parenthesis(text):
    import re
    if not text:
        return text
    chains_between_parenthesis = re.findall(r"\((.*?)\)", text)
    for chain in chains_between_parenthesis:
        is_upper = is_every_upper(chain)
        if not is_upper:
            text = text.replace(f"({chain})", "")
    text = text.replace("/", " / ")
    text = text.replace(",", " , ")
    text = re.sub(r' +', ' ', text)
    text = text.replace(" ,", ",")
    return text.strip()


def special_normalizer(text, delete_parenthesis=True):
    if not text:
        return text
    # delete all inside parenthesis:
    if delete_parenthesis:
        text = delete_non_upper_parenthesis(text)
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text_normalizer(text)
    text = text.replace("METFORMINA LINAGLIPTINA", "LINAGLIPTINA METFORMINA")
    text = text.replace("LEVOTIROXINA SODICA", "LEVOTIROXINA")
    return text.strip()


def get_pdf_data():
    process = ProcessPDF(main_files["pdf"])
    process(800)
    # process(pages_range=(79, 350))
    # save json in a file:
    process.save_json(main_files["json"])


def get_pdf_nutrition():
    process = ProcessPDF(
        nutri_files["pdf"], json_path=nutri_files["json"], is_nutrition=True)
    process(150)
    process.save_json()


def move_components():
    from report.models import Supply
    from medicine.models import Presentation, Component
    from intl_medicine.models import PrioritizedComponent
    comps = [
        ('AMINOACIDOS CRISTALINOS', 'AMINOÁCIDOS CRISTALINOS'),
        ('METFORMINA/ GLIMEPIRIDA', 'METFORMINA/GLIMEPIRIDA'),
        ('AMOXICILINA-ACIDO CLAVULANICO', 'AMOXICILINA/ÁCIDO CLAVULÁNICO'),
        # ('BROMURO DE TIOTROPIO', ),
        ("TIOTROPIO BROMURO", "BROMURO DE TIOTROPIO"),
        ("SEVELAMERO", "SEVELÁMERO"),
        ("SOLUCIÓN PARA DIALISIS PERITONEAL", "SOLUCIÓN PARA DIÁLISIS PERITONEAL"),
        ('BUSULFANO', 'BUSULFÁN'),
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
            good_alias = good_comp.alias.split(",") if good_comp.alias else []
            good_alias = set([n.strip() for n in good_alias])
            bad_alias = bad_comp.alias.split(",") if bad_comp.alias else []
            bad_alias = set([n.strip() for n in bad_alias])
            all_alias = good_alias | bad_alias
            if all_alias:
                good_comp.alias = ", ".join(all_alias)
            if len(all_names) > 1:
                good_comp.alternative_names = list(all_names)
                good_comp.save()
            Presentation.objects.filter(component=bad_comp) \
                .update(component=good_comp)
            Supply.objects.filter(component=bad_comp) \
                .update(component=good_comp)
            bad_pc = PrioritizedComponent.objects.filter(
                component=bad_comp).first()
            if bad_pc:
                if bad_pc.is_prioritized:
                    PrioritizedComponent.objects.filter(component=good_comp) \
                        .update(is_prioritized=True)
                bad_pc.delete()
            bad_comp.name = 'BORRADO'
            bad_comp.short_name = None
            bad_comp.group = None
            bad_comp.save()
        else:
            print("ERROR moving", comp)


def small_cleans():
    move_components()
    cleans = [
        # ("BUSULFANO", "BUSULFAN"),
        ("LEUPROLIDA", "LEUPRORELINA"),
        ('SUBSALICILATO DE BISMUTO', 'BISMUTO'),
        # ("LEVOTIROXINA SODICA", "LEVOTIROXINA"),
        # ("TIOTROPIO BROMURO", "BROMURO DE TIOTROPIO")
    ]
    for clean in cleans:
        models.Component.objects.filter(name=clean[0]).update(name=clean[1])
    asparta = models.Component.objects.filter(
        name__contains="ASPARTA SOLUBLE").first()
    if asparta:
        asparta.alternative_names = [asparta.name]
        asparta.name = "INSULINA ASPARTA"
        asparta.save()


def get_containers(component, source='pdf'):
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
        elif source == 'web':
            for container in comp['keys']:
                containers.append(container)
    return containers


def get_component_keys(component, source='pdf'):
    keys = []
    if not component:
        return keys
    containers = get_containers(component, source)
    for container in containers:
        if source == 'saved':
            keys.append(container.key[4:])
        else:
            keys.append(container['key'][4:])
    return keys


def get_symbols(saved, pdf, web, original_symbol=None, special=False):
    from statistics import mode

    def normalizer(txt):
        return special_normalizer(txt, delete_parenthesis=special)
    if special:
        saved = delete_non_upper_parenthesis(saved)
        pdf = delete_non_upper_parenthesis(pdf)
        web = delete_non_upper_parenthesis(web)
    values = [web, pdf, saved]
    web_norm = normalizer(web)
    pdf_norm = normalizer(pdf)
    saved_norm = normalizer(saved)
    values_norm = [web_norm, pdf_norm, saved_norm]
    real_values = [v for v in values if v]
    final_values = real_values.copy()
    ordered_values = [saved, pdf, web]
    ordered_norm = [saved_norm, pdf_norm, web_norm]
    real_len = len(real_values)
    if not real_values:
        return ["⭕", "⭕|⭕|⭕"], None
    uniques = {u for u in real_values}
    need_special = False
    if special and len(uniques) > 1 and real_len > 1:
        need_special = True
        real_values = [v for v in values_norm if v]
        uniques = {u for u in real_values if u}

    symbol = "❌"
    final_value = None
    second_symbols = []
    # number = f"{real_len}️⃣"
    number = f"{real_len}️⃣"
    if len(uniques) == 1:
        if real_len == 1:
            symbol = "️✴️"
        elif real_len == 2:
            symbol = "❇️"
        else:
            symbol = "✅"
        final_value = web or pdf or saved
        for v in ordered_values:
            second_symbols.append("✅" if v else "⭕")
    elif len(uniques) == 2 and real_len == 3:
        symbol = "❇️"
        common = mode(real_values)
        for v in ordered_values:
            final_text = normalizer(v) if need_special else v
            second_symbols.append("✅" if final_text == common else "✴️")
        for text in values:
            final_text = normalizer(text) if need_special else text
            if final_text == common:
                final_value = text
                break
    elif web:
        if saved_norm and web_norm in saved_norm:
            symbol = "✴️"
            final_value = saved
            second_symbols = ["✅", "✴️" if pdf else "⭕", "✳️"]
        if pdf_norm and web_norm in pdf_norm:
            symbol = "❇️"
            final_value = pdf
            second_symbols = ["✴️" if saved else "⭕", "✅", "✳️"]
    if not final_value and pdf:
        if saved_norm and pdf_norm in saved_norm:
            symbol = "✴️"
            final_value = saved
            second_symbols = ["✅", "✴️", "✳️" if web else "⭕"]
        if web_norm and pdf_norm in web_norm:
            symbol = "❇️"
            final_value = web
            second_symbols = ["✴️", "✳️" if saved else "⭕", "✅"]

    if not final_value:
        for v in ordered_values:
            second_symbols.append("✴️" if v else "⭕")
    second_symbol = "|".join(second_symbols)
    first_symbol = f"{number}{symbol}"
    if original_symbol:
        first_symbol = f"{original_symbol}{first_symbol}"
    return [first_symbol, second_symbol], final_value


class BuildNewTable:

    def __init__(self, is_explore=True):
        from intl_medicine.models import Respondent, GroupAnswer
        # read json from a file (json_path):
        with open(main_files["json"], "r", encoding="utf-8") as file:
            self.all_components = json.load(file)
            print("len(all_components)", len(self.all_components))
        self.saved_groups = None
        self.is_explore = is_explore
        self.pdf_components = {}
        self.pdf_containers = {}
        self.saved_containers = {}
        self.web_containers = {}
        self.saved_components = {}
        self.web_components = {}
        self.csv = io.StringIO()
        self.csv_mini = io.StringIO()
        self.buffer = csv.writer(self.csv, delimiter="|")
        self.buffer_mini = csv.writer(self.csv_mini, delimiter="|")
        self.unique_components = set()
        self.ready_components = set()
        self.last_symbol = None
        self.current_comp_name = None
        self.warnings = {"many": [], "no": []}
        self.scrapper = Scrapper()
        self.example_prints = 0
        self.respondent, _ = Respondent.objects.get_or_create(
            email="nuevo@nuevo.com", first_name="Nuevo", last_name="Nuevo",
            token="nuevo", institution="Nuevo", position="Nuevo")
        GroupAnswer.objects.filter(respondent=self.respondent).delete()
        self.new_componentes = []

    def __call__(self):
        small_cleans()
        self.build_first_objects()
        # self.analyze_components()
        # self.save_csv()

    def build_first_objects(self):
        # 010.000.0101.00
        for comp in self.all_components:
            comp_name = special_normalizer(comp['name'], True)
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
            name = special_normalizer(comp.name, True)
            self.unique_components.add(name)
            self.saved_components.setdefault(name, [])
            self.saved_components[name].append(comp)
        for comp in self.scrapper.all_components:
            name = special_normalizer(comp['name'], True)
            # self.unique_components.add(name)
            self.web_components.setdefault(name, [])
            self.web_components[name].append(comp)
            for container in comp['keys']:
                key = container['key']
                id_key = key[4:]
                container['component'] = comp
                self.web_containers.setdefault(id_key, [])
                self.web_containers[id_key].append(container)

        for container in models.Container.objects.all():
            key = container.key[4:]
            self.saved_containers[key] = container

        saved_groups = models.Group.objects.all().values("name", "id")
        self.saved_groups = {special_normalizer(g["name"]): g["id"]
                             for g in saved_groups}

    def analyze_components(self):
        ordered_components = sorted(list(self.unique_components))
        # self.scrapper.build_all_keys()
        for comp_name in ordered_components:
            self.current_comp_name = comp_name
            if comp_name in self.ready_components:
                continue
            self.analyze_component(comp_name)

    def analyze_component(self, comp_name):
        from intl_medicine.models import (
            PrioritizedComponent, Component, GroupAnswer)
        from medicine.models import Group
        saved_comp = self.saved_components.get(comp_name)
        pdf_comp = self.pdf_components.get(comp_name)
        web_comp = self.web_components.get(comp_name)

        if not saved_comp and not pdf_comp and not web_comp:
            print("not found any:", comp_name)
            return
        symbol = None
        # comp_id = None

        if not pdf_comp:
            saved_keys = get_component_keys(saved_comp, source='saved')
            web_keys = get_component_keys(web_comp, source='web')
            all_keys = set(saved_keys + web_keys)
            for key in all_keys:
                if pdf_container := self.pdf_containers.get(key):
                    # print("pdf_container", pdf_container)
                    new_comp_name = pdf_container[0]['presentation']['component']['name']
                    pdf_comp = self.get_component(
                        new_comp_name, source='pdf', key=key)
                    if pdf_comp:
                        symbol = "⚠️"
                        break
        if not saved_comp:
            pdf_keys = get_component_keys(pdf_comp, source='pdf')
            web_keys = get_component_keys(web_comp, source='web')
            all_keys = set(pdf_keys + web_keys)
            for key in all_keys:
                if saved_container := self.saved_containers.get(key):
                    # print("saved_container", saved_container)
                    component = saved_container.presentation.component
                    saved_comp = self.get_component(
                        component.name, source='saved', key=key)
                    if saved_comp:
                        # symbol = "⇼"
                        symbol = "⚠️"
                        break
        if not web_comp:
            pdf_keys = get_component_keys(pdf_comp, source='pdf')
            saved_keys = get_component_keys(saved_comp, source='saved')
            all_keys = set(pdf_keys + saved_keys)
            for key in all_keys:
                if web_container := self.web_containers.get(key):
                    new_comp_name = web_container[0]['component']['name']
                    web_comp = self.get_component(
                        new_comp_name, source='web', key=key)
                    if web_comp:
                        symbol = "⚠️"
                        break

        real_name, _ = self.get_real_name(pdf_comp, source='pdf')
        saved_name, comp_id = self.get_real_name(saved_comp, source='saved')
        web_name, _ = self.get_real_name(web_comp, source='web')

        symbols, final_value = get_symbols(
            saved_name, real_name, web_name, symbol, special=True)
        row = ['component', 'name', comp_id, saved_name, real_name, web_name]
        row.extend(symbols)
        row.append(final_value)
        self.ready_components.add(comp_name)
        self.buffer.writerow([""]*9)
        self.buffer.writerow(row)
        container_rows, groups = self.analyze_containers(
            saved_comp, pdf_comp, web_comp)
        if self.is_explore:
            groups = []

        for group_name in groups:
            if comp_id:
                # print("comp_id:", comp_id)
                component_obj = Component.objects.get(id=comp_id)
                is_new = False
            else:
                component_obj, is_new = Component.objects.get_or_create(
                    name=final_value)
                if is_new:
                    self.new_componentes.append(component_obj)
            if not is_new and final_value and component_obj.name != final_value:
                all_names = component_obj.alternative_names or []
                if component_obj.interactions:
                    all_names.append(component_obj.interactions)
                if component_obj.short_name:
                    all_names.append(component_obj.short_name)
                all_names.append(component_obj.name)
                all_names = set(all_names)
                if len(all_names) > 1:
                    component_obj.alternative_names = list(all_names)
                component_obj.interactions = (
                    component_obj.interactions or component_obj.name)
                component_obj.name = final_value
                component_obj.save()
            group_id = self.saved_groups.get(group_name)
            if not group_id:
                new_group, is_new = Group.objects.get_or_create(
                    name=group_name)
                if is_new:
                    self.saved_groups[group_name] = new_group.id
                group_id = new_group.id
            # cont_id = cont_row[2]
            if component_obj and group_id:
                group_answer, _ = GroupAnswer.objects.get_or_create(
                    respondent=self.respondent, group_id=group_id)
                is_prioritized = None
                saved_group_answer = GroupAnswer.objects.filter(
                    respondent=None, group_id=group_id).first()
                if saved_group_answer:
                    saved_pc = PrioritizedComponent.objects.filter(
                        group_answer=saved_group_answer,
                        component=component_obj).first()
                    if saved_pc:
                        is_prioritized = saved_pc.is_prioritized
                pc, is_new_pc = PrioritizedComponent.objects.get_or_create(
                    group_answer=group_answer, component=component_obj)
                if is_new_pc:
                    pc.is_prioritized = is_prioritized
                    pc.save()
                else:
                    if is_prioritized and pc.is_prioritized != is_prioritized:
                        print(f"ERROR in is_prioritized, se tenía"
                              f"{pc.is_prioritized} y hay{is_prioritized}"
                              f" pc_id: {pc.id}")

        rows = [row] + container_rows
        # some_error = [r for r in rows if "⭕" in r[6] or "❌" in r[6]]
        some_error = [r for r in rows if "❌" in r[6]]
        if some_error:
            self.buffer_mini.writerow([""]*9)
            self.buffer_mini.writerows(rows)

    def write_container_row(self, pdf_cont, saved_cont, web_cont, field):
        name = field['name']
        is_group = name == 'groups'
        is_pres = field.get('is_pres')
        pdf_value = None
        saved_value = None
        web_value = None
        symbol = None
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
                        values.append(value.strip())
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
        if web_cont:
            if is_pres:
                if is_group:
                    groups = [elem['component']['group_name']
                              for elem in web_cont]
                    text_groups = [special_normalizer(g) for g in groups]
                    text_groups = sorted(set(text_groups))
                    web_value = ", ".join(text_groups)
                else:
                    web_value = web_cont[0][fields[2]]
            else:
                web_value = web_cont[0][fields[2]]

        symbols, final_value = get_symbols(saved_value, pdf_value, web_value)
        row = [field['title'], name, elem_id, saved_value, pdf_value, web_value]
        row.extend(symbols)
        row.append(final_value)
        self.buffer.writerow(row)
        return row

    def analyze_containers(self, saved_comp, pdf_comp, web_comp):
        all_keys = set()

        pdf_containers = get_containers(pdf_comp, source='pdf')
        all_keys.update({c['key'][4:] for c in pdf_containers})
        saved_containers = get_containers(saved_comp, source='saved')
        all_keys.update({c.key[4:] for c in saved_containers})
        web_containers = get_containers(web_comp, source='web')
        all_keys.update({c['key'][4:] for c in web_containers})
        # all_keys.update({c[4:] for c in self.scrapper.all_keys.keys()})
        all_keys = sorted(list(all_keys))

        # fields = [
        #     {'row_names': ['  container', 'key'], 'fields': ('key', 'key')},
        #     {'row_names': ['  ', 'text'], 'fields': ('description', 'name')},
        #     {'row_names': ['  ', 'groups'], 'fields': ('description', 'name')},
        # ]
        fields = [
            {
                'title': '   container', 'name': 'key',
                'fields': ('key', 'key', 'key')
            },
            {
                'title': '', 'name': 'text',
                'fields': ('description', 'name', 'container_description')
            },
            {
                'title': '      present', 'name': 'name', 'is_pres': True,
                'fields': ('name', 'presentation_type_raw', 'presentation_name')
            },
            {
                'title': '', 'name': 'text', 'is_pres': True,
                'fields': ('description', 'description', 'presentation_description')
            },
            {'title': '', 'name': 'groups', 'is_pres': True},
        ]
        rows = []
        all_groups = set()
        for short_key in all_keys:
            pdf_container = self.pdf_containers.get(short_key)
            saved_container = self.saved_containers.get(short_key)
            web_container = self.web_containers.get(short_key)
            for field_data in fields:
                row = self.write_container_row(
                    pdf_container, saved_container, web_container, field_data)
                rows.append(row)
                if field_data['name'] == 'groups':
                    groups = row[4]
                    if groups:
                        groups = groups.split(", ")
                        for group in groups:
                            all_groups.add(group)
        return rows, all_groups

    def get_component(self, comp_name, source='pdf', key=None):
        if source == 'pdf':
            origin = self.saved_components
            destination = self.pdf_components
        else:
            origin = self.pdf_components
            destination = self.saved_components
        comp_name = special_normalizer(comp_name, delete_parenthesis=True)
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

    def get_real_name(self, comp, source='pdf'):
        if not comp:
            return None, None
        if source == 'saved':
            real_names = {delete_non_upper_parenthesis(p.name) for p in comp}
            ids = {p.id for p in comp}
            if len(ids) > 1:
                print(f"ERROR en MANY: {source}; ids: ", ids, real_names)
                self.warnings['many'].append(f"{source}; {ids}")
                # elem_id = "many"
            elem_id = ids.pop()
        else:
            real_names = {delete_non_upper_parenthesis(p['name']) for p in comp}
            elem_id = None

        cleaned_names = {special_normalizer(n, True) for n in real_names}
        if len(cleaned_names) > 1:
            print("ERROR en MANY: saved; names: ", real_names)
            self.warnings['many'].append(f"{source}; {real_names}")
        return real_names.pop(), elem_id

    def save_csv(self, path=None, encoding="utf-8"):
        final_path = path or main_files["csv"]
        with open(final_path, "w", encoding=encoding, newline="") as file:
            file.write(self.csv.getvalue())

    def save_mini_csv(self, path=None, encoding="utf-8"):
        if path:
            final_path = path
        else:
            final_path = main_files["csv"].replace(".csv", "_mini.csv")
        with open(final_path, "w", encoding=encoding, newline="") as file:
            file.write(self.csv_mini.getvalue())

    def analyze_groups(self):

        pdf_groups = set()
        for comp in self.all_components:
            group = comp['group']
            group = special_normalizer(group)
            if group:
                pdf_groups.add(group)

        saved_groups = models.Group.objects.all().values_list("name", flat=True)
        saved_groups = [special_normalizer(group) for group in saved_groups]
        saved_groups = set(saved_groups)

        web_groups = set()
        for component in self.scrapper.all_components:
            group = component['group_name']
            if group:
                group = special_normalizer(group)
                if group:
                    web_groups.add(group)

        all_groups = pdf_groups | saved_groups | web_groups
        all_groups = sorted(list(all_groups))
        self.buffer.writerow(["group", "pdf", "saved", "web"])
        for group in all_groups:
            pdf_group = group in pdf_groups
            saved_group = group in saved_groups
            web_group = group in web_groups
            row = [group, pdf_group, saved_group, web_group]
            self.buffer.writerow(row)


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
