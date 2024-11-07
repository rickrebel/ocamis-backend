import csv
import json
from collections import defaultdict
from os import path
from pprint import pprint
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand
from django.db.models import Q
from unidecode import unidecode

from category.models import StatusControl
from medicine.models import Component, Container, Group, Presentation


class Command(BaseCommand):

    medicine_blocks: List = []
    groups_not_match = []

    def add_arguments(self, parser):
        parser.add_argument("--path_file", type=str)

    def handle(self, *args, path_file: Optional[str] = None, **kwargs):
        # comprovar si existe el archivo en sistema, validar path_file
        if not path_file or not path.exists(path_file):
            print(f"El archivo {path_file} no existe")
            return

        self.groups_not_match = []

        self.load_file(path_file)

        self.update_medicines()

        self.groups_not_match_report()

    def load_file(self, path_file):
        self.medicine_blocks = []
        with open(path_file, mode="r", encoding="utf-8") as archivo_csv:
            # Utiliza DictReader para leer el CSV como diccionarios
            medicine_data = csv.DictReader(archivo_csv, delimiter="|")
            block = []
            for row in medicine_data:
                if not row.get("field"):
                    self.clean_block_data(block)
                    block = []
                    continue

                block.append(row)

            self.clean_block_data(block)

    def clean_block_data(self, block: List[Dict[str, str]]):
        if not block:
            return
        if block[0].get("model", "").strip() != "component":
            # No tiene el formato esperado, el primero debe ser un componente
            return

        # headers:  model|field|id|saved_name|pdf|web|summary_icons|detail_icons|final
        component = block.pop(0)
        block_data = {
            "component":
            {
                "id": component.get("id"),
                component.get("field"): dict(
                    saved_name=component.get("saved_name"),
                    pdf=component.get("pdf"),
                    web=component.get("web"),
                    final=component.get("final"),
                    summary_icons=component.get("summary_icons"),
                    detail_icons=component.get("detail_icons"),
                ),
            },
            "presentations": [],
        }

        actual_key = ""
        containers = []
        container_data = {}

        while block:
            row = block.pop(0)
            model = row.get("model", "").strip()
            if model and model != actual_key:
                actual_key = model
                if actual_key == "container":
                    if container_data:
                        containers.append(container_data)
                    container_data = {
                        "container": {},
                        "present": {}
                    }

            container_data[actual_key][row.get("field")] = dict(
                saved_data=row.get("saved_name"),
                pdf=row.get("pdf"),
                web=row.get("web"),
                final=row.get("final"),
                summary_icons=row.get("summary_icons"),
                detail_icons=row.get("detail_icons"),
            )

            if model:
                container_data[actual_key]["id"] = row.get("id")

        if container_data:
            containers.append(container_data)

        unique_presents = defaultdict(lambda: {'containers': []})
        for container_data in containers:
            present = container_data.get("present")
            container = container_data.get("container")
            present_key = json.dumps(present, sort_keys=True)
            unique_presents[present_key]['present'] = present
            unique_presents[present_key]['containers'].append(container)

        block_data["presentations"] = list(unique_presents.values())

        self.medicine_blocks.append(block_data)

    def update_medicines(self):
        for block_data in self.medicine_blocks:
            component_data = block_data.get("component")
            try:
                component = self.update_component(component_data)
            except Component.DoesNotExist:
                print(f"Componente no encontrado {component_data.get('id')}")
                continue

            self.update_presentations(
                block_data.get("presentations"),
                component
            )

    def update_component(self, componet_data: Dict) -> Component:
        component_id = componet_data.get("id", None)
        name_data = componet_data.get("name")
        if not name_data:
            raise ValueError("El componente no tiene nombre")

        if component_id:
            component = Component.objects.get(id=component_id)
        else:
            name = get_priority_value(name_data)
            component, _ = Component.objects.get_or_create(name=name)

        for attribute, data in componet_data.items():
            if attribute in ["id", "groups"]:
                continue
            attribute_value = get_priority_value(data, attribute, component)
            setattr(component, attribute, attribute_value)

        component.source_data = componet_data  # type: ignore

        component.save()
        return component

    def update_presentation(
            self, presentation_data: Dict, component: Component
    ) -> Presentation:
        presentation_id = presentation_data.get("id", None)
        is_created = False
        if presentation_id:
            presentation = Presentation.objects.get(id=presentation_id)
        else:
            name = get_priority_value(
                presentation_data.get("name", {}), "name")
            text = get_priority_value(
                presentation_data.get("text", {}), "text")
            presentation, is_created = Presentation.objects.get_or_create(
                description=text,
                presentation_type_raw=name,
                component=component
            )

        for attribute, data in presentation_data.items():
            if attribute in ["id", "groups"]:
                continue
            attribute_value = get_priority_value(data, attribute, presentation)
            setattr(presentation, attribute, attribute_value)

        groups = get_priority_value(
            presentation_data.get("groups", {}), "groups")

        u_groups = unidecode(groups or "").lower().strip()

        if u_groups and is_created:
            group_obj, _ = Group.objects.get_or_create(
                unidecode_name=u_groups, defaults={"name": groups})
            presentation.groups.add(group_obj)
        elif u_groups:
            group_obj = Group.objects.filter(unidecode_name=u_groups).first()
            if not group_obj:
                self.groups_not_match.append(
                    {
                        "presentation": presentation, "group": None,
                        "message": "presentation preexistente "
                        f"No coincide con el grupo actual (no existe) {u_groups}"
                    }
                )
            elif not presentation.groups.filter(id=group_obj.pk).exists():
                self.groups_not_match.append(
                    {
                        "presentation": presentation, "group": group_obj,
                        "message": "presentation preexistente "
                        "No coincide con el grupo actual"
                    }
                )

        presentation.source_data = presentation_data  # type: ignore

        presentation.save()
        return presentation

    def update_container(
            self, container_data: Dict, presentation: Presentation
    ) -> Optional[Container]:
        container_id = container_data.get("id", None)
        if container_id:
            container = Container.objects.get(id=container_id)
        else:
            key = get_priority_value(container_data.get("key", {}), "key")
            try:
                container, _ = Container.objects.get_or_create(
                    presentation=presentation, key=key
                )
            except Exception as e:
                print(f"Error al crear container {e}")
                print(f"presentation: {presentation}")
                print(f"key: {key}")
                print()
                return

        for attribute, data in container_data.items():
            if attribute in ["id", "groups"]:
                continue
            attribute_value = get_priority_value(data, attribute, container)
            setattr(container, attribute, attribute_value)

        container.source_data = container_data  # type: ignore

        container.save()
        return container

    def update_presentations(self, presentations_list: Dict, component: Component):
        for presentation_tuple in presentations_list:
            presentation_data = presentation_tuple.get("present")
            containers_data = presentation_tuple.get("containers")
            presentation = self.update_presentation(
                presentation_data, component)
            for container_data in containers_data:
                self.update_container(container_data, presentation)

            """
            Penúltimo paso. status_final en Presentation y Component 
            Primero asignaremos un valor de status_final a Presentación, para eso,
            buscaremos el valor más bajo de “order” entre todos los status_review
            de sus Container, así como el status_review de el mismo registro. 
            El resultado será el menor valor de order encontrado (obvio el 
            StatusControl que le corresponda)
            """
            pres_status_final = StatusControl.objects\
                .filter(containers_review__presentation=presentation)\
                .order_by('order').first()

            presentation.status_final = pres_status_final
            presentation.save()

        """
        Una vez hecho eso, aplicaremos casi la misma lógica para Componente, 
        a partir del valor de status_final de todas sus Presentaciones y el 
        valor de status_review del mismo registro comonente.
        """

        status_final = StatusControl.objects\
            .filter(
                Q(presentations_final__component=component) |
                Q(components_review__id=component.pk)
            )\
            .order_by('order').first()

        component.status_final = status_final
        component.save()

    def groups_not_match_report(self):
        """
        {
            "presentation": presentation, "group": group_obj,
            "message": "presentation preexistente "
            "No coincide con el grupo actual"
        }
        """
        for item in self.groups_not_match:
            presentation = item["presentation"]
            group = item["group"]
            grups_names = ",".join(
                presentation.groups.values_list("name", flat=True))
            full_message = (
                f"{item['message']} - presentation: {grups_names} -"
                f"Grupo actual: {item['group'].name}" if group else ""
            )
            self.stderr.write(self.style.ERROR(full_message))

            prex_notes = presentation.component.notes or ""
            if prex_notes:
                full_message = f"{prex_notes}\n{full_message}"
            presentation.component.notes = full_message
            presentation.component.save()


def get_priority_value(data: dict, attribute: str = "", obj=None):
    return (
        data.get("final") or
        getattr(obj, attribute, None) or
        data.get("pdf") or
        data.get("saved_name") or
        data.get("web")
    )
