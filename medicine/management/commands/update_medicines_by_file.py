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
from medicine.views import equivalences


class Command(BaseCommand):

    medicine_blocks: List = []
    groups_not_match = []
    summary_icons_dict = {item["summary_icons"]: item["status_final_id"]
                          for item in equivalences}

    def add_arguments(self, parser):
        parser.add_argument("--path_file", type=str)

    def handle(self, *args, path_file: Optional[str] = None, **kwargs):
        # comprobar si existe el archivo en sistema, validar path_file
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

            field = row.get("field")
            if actual_key == "present":
                if field == "name":
                    field = "description"
                elif field == "text":
                    field = "presentation_type_raw"
            container_data[actual_key][field] = dict(
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

    def generic_update(self, data: Dict, instance):
        all_review_status = set()
        for attribute, values in data.items():
            if attribute in ["id", "groups"]:
                continue
            if summary_icons := values.get("summary_icons"):
                all_review_status.add(self.summary_icons_dict.get(summary_icons))
            attribute_value = get_priority_value(values, attribute, instance)
            setattr(instance, attribute, attribute_value)

        smaller_status_control = StatusControl.objects.filter(
            name__in=all_review_status).order_by('order').first()
        if not instance.status_review:
            instance.status_review = smaller_status_control
        elif smaller_status_control.order < instance.status_review.order:
            instance.status_review = smaller_status_control
        instance.source_data = data
        instance.save()
        return instance

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

        return self.generic_update(componet_data, component)

    def update_presentation(
            self, presentation_data: Dict, component: Component
    ) -> Presentation:
        presentation_id = presentation_data.get("id", None)
        is_created = False
        review_status = False
        if presentation_id:
            presentation = Presentation.objects.get(id=presentation_id)
        else:
            presentation_type_raw = get_priority_value(
                presentation_data.get("presentation_type_raw", {}),
                "presentation_type_raw")
            description = get_priority_value(
                presentation_data.get("description", {}), "description")
            if not presentation_type_raw:
                presentation_type_raw = "tipo de presentación no especificado".upper()
                review_status = True
            if not description:
                description = "composición no especificada".upper()
                review_status = True

            presentation, is_created = Presentation.objects.get_or_create(
                description=description,
                presentation_type_raw=presentation_type_raw,
                component=component
            )

            if review_status:
                presentation.status_review_id = "required_review"

        groups = get_priority_value(
            presentation_data.get("groups", {}), "groups")

        u_groups = unidecode(groups or "").lower().strip()

        if u_groups and is_created:
            try:
                group_obj = Group.objects.get(
                    unidecode_name=u_groups, defaults={"name": groups})
                presentation.groups.add(group_obj)
            except Group.DoesNotExist:
                self.groups_not_match.append(
                    {
                        "presentation": presentation, "group": None,
                        "message": "presentation nueva "
                        f"No coincide con el grupo actual (no existe) {u_groups}"
                    }
                )
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

        return self.generic_update(presentation_data, presentation)

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

        return self.generic_update(container_data, container)

    def update_presentations(self, presentations_list: Dict, component: Component):
        for presentation_tuple in presentations_list:
            presentation_data = presentation_tuple.get("present")
            containers_data = presentation_tuple.get("containers")
            try:
                presentation = self.update_presentation(
                    presentation_data, component)
            except Exception as e:
                continue

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
            if not pres_status_final:
                print(f"Error al obtener status_final para {presentation}")
            elif not presentation.status_final:
                presentation.status_final = pres_status_final
            elif pres_status_final.order < presentation.status_review.order:
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
        if not component.status_review:
            component.status_final = status_final
        elif status_final.order < component.status_review.order:
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
            groups_names = ",".join(
                presentation.groups.values_list("name", flat=True))
            full_message = (
                f"{item['message']} - presentation: {groups_names} -"
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

# Error al crear container el valor es demasiado largo para el tipo character varying(20)
#
# presentation: LITIO
# key: Envase con 100 tabletas
#
# Error al obtener status_final para LITIO
