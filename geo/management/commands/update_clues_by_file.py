from datetime import datetime
from pprint import pprint
import re
from typing import List, Optional

import pandas as pd
from pandas import DataFrame
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from geo.models import CLUES, Institution, Municipality, State


def clean_na(row):
    cols = row.tolist()
    return [col.strip() if isinstance(col, str) else "" for col in cols]


equivalences = [
    ("CLUES", "clues"),
    ("CLAVE DEL MUNICIPIO", "municipality_inegi_code"),
    ("LOCALIDAD", "locality"),
    ("CLAVE DE LA LOCALIDAD", "locality_inegi_code"),
    ("JURISDICCION", "jurisdiction"),
    ("CLAVE DE LA JURISDICCION", "jurisdiction_clave"),
    ("NOMBRE TIPO ESTABLECIMIENTO", "establishment_type"),
    ("NOMBRE DE TIPOLOGIA", "typology"),
    ("CLAVE DE TIPOLOGIA", "typology_cve"),
    ("NOMBRE DE LA UNIDAD", "name"),
    ("TIPO DE VIALIDAD", "type_street"),
    ("VIALIDAD", "street"),
    ("CODIGO POSTAL", "postal_code"),
    ("ESTATUS DE OPERACION", "status_operation"),
    ("RFC DEL ESTABLECIMIENTO", "rfc"),
    ("LATITUD", "longitude"),
    ("LONGITUD", "latitude"),
    ("NOMBRE DE LA INS ADM", "admin_institution"),
    ("NIVEL ATENCION", "atention_level"),
    ("ESTRATO UNIDAD", "stratum"),
]

integers_equivalences = [
    ("CONSULTORIOS DE MED GRAL", "consultings_general"),
    ("CONSULTORIOS EN OTRAS AREAS", "consultings_other"),
    ("CAMAS EN AREA DE HOS", "beds_hopital"),
    ("CAMAS EN OTRAS AREAS", "beds_other"),
]


class Command(BaseCommand):

    help = "Reads an excel file and updates the database"

    def add_arguments(self, parser):
        # file_path optional argument
        parser.add_argument(
            "--file_path", type=str, help="Excel file path")
        parser.add_argument(
            "--sheet_name", type=str, help="Sheet name in the excel file")

    def handle(self, *args, **options):
        file_path = options["file_path"]
        sheet_name = options["sheet_name"] or "CLUES_202408"

        if not file_path:
            file_path = getattr(settings, "DRAFT_CLUES_FILE_PATH", None)

        if not file_path:
            raise ValueError("File path not provided")

        self.load_geo_data()

        self.stdout.write(self.style.SUCCESS("Reading excel file..."))

        excel_file = pd.ExcelFile(file_path)
        data_excel = excel_file.parse(
            sheet_name, dtype="string", na_filter=False, keep_default_na=False
        )

        self.read_excel(data_excel)

        pprint(self.geo_errors)

    def load_geo_data(self):
        self.geo_errors = {
            "institution": [],
            "state": [],
            "municipality": [],
        }
        self.stdout.write(self.style.SUCCESS("Loading geo data..."))
        all_states = State.objects.all()
        self.state_dict = {state.inegi_code: state.id for state in all_states}

        all_municipalities = Municipality.objects.all()
        self.municipality_dict = {
            f"{mun.state.inegi_code}-{mun.inegi_code}": mun.pk
            for mun in all_municipalities
        }

        all_institutions = Institution.objects.all()
        self.institution_dict = {}
        for institution in all_institutions:
            for code in institution.get_codes_list():
                self.institution_dict[code] = institution.pk

        self.institution_dict["SSA"] = self.institution_dict["INSABI"]

        self.sum_fields = {
            "total_unities": [
                # "CONSULTORIOS DE MED GRAL",
                # "CONSULTORIOS EN OTRAS AREAS",
                # "CAMAS EN AREA DE HOS",
                # "CAMAS EN OTRAS AREAS",
            ],
        }

        self.concat_fields = {
            "sheet_number": ["NUMERO EXTERIOR", "NUMERO INTERIOR"],
            "suburb": ["TIPO DE ASENTAMIENTO", "ASENTAMIENTO"],
        }

        self.codes = ["SMP", "HUN", "CIJ", "CRO"]
        self.establishment_types = ["DE APOYO", "DE ASISTENCIA SOCIAL"]
        self.typologies = ["BS", "X", "P", "UMM"]

        self.stdout.write(self.style.SUCCESS("Geo data loaded"))

    def read_excel(self, data_excel: DataFrame):

        headers = data_excel.columns
        self.stdout.write(self.style.SUCCESS("headers found"))

        self.new_institutions_names = {}

        iter_data = data_excel.apply(clean_na, axis=1)
        list_val = iter_data.tolist()
        if not list_val:
            raise ValueError("No data found in the excel file")

        self.check_equivalences(headers)

        for row in list_val:
            if len(row) < len(headers):
                row += [''] * (len(headers) - len(row))
            row_dict = dict(zip(headers, row[:len(headers)]))
            self.match_data(row_dict)

        self.update_institutions_names()

    def match_data(self, row_dict: dict):
        clues_key = row_dict.get("CLUES")
        clues = self.get_clues(row_dict)
        if not clues:
            return

        last_change = row_dict.get("FECHA ULTIMO MOVIMIENTO")

        if last_change:
            date_change = datetime.strptime(last_change, "%d/%m/%Y")
            date_change = timezone.make_aware(date_change)
            clues.last_change = date_change

        for xls_field, model_field in equivalences:
            setattr(clues, model_field, row_dict[xls_field])

        for xls_field, model_field in integers_equivalences:
            field_value = row_dict.get(xls_field, 0)
            if field_value:
                setattr(clues, model_field, int(field_value))
            else:
                if getattr(clues, model_field) is None:
                    setattr(clues, model_field, 0)

        for field in self.sum_fields:
            field_value = sum(
                [int(row_dict.get(sub_field, 0))
                 for sub_field in self.sum_fields[field]])
            if field_value:
                setattr(clues, field, field_value)
            else:
                if getattr(clues, field) is None:
                    setattr(clues, field, 0)

        for field in self.concat_fields:
            setattr(clues, field, " ".join(
                [row_dict.get(sub_field, "")
                 for sub_field in self.concat_fields[field]]))

        real_name = clues.name
        if real_name.startswith(clues.typology_cve):
            real_name = real_name[len(clues.typology_cve):]
            real_name = real_name.strip()
        arr_nums = re.findall(r"\d+", real_name)
        if arr_nums:
            clues.number_unity = arr_nums[0]

        if clues.status_operation == "EN OPERACION":
            if clues.institution.code in self.codes:
                clues.is_active = False
            elif clues.establishment_type in self.establishment_types:
                clues.is_active = False
            elif clues.typology_cve in self.typologies:
                clues.is_active = False
            else:
                clues.is_active = True
        else:
            clues.is_active = False


        try:
            clues.save()
        except Exception as e:
            try:
                clues.full_clean()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error validating clues {clues_key}: {e}"))
                return
            self.stdout.write(
                self.style.ERROR(f"Error saving clues {clues_key}: {e}"))

    def get_clues(self, row_dict: dict) -> Optional[CLUES]:
        clues_key = row_dict.get("CLUES")

        clave_inst = row_dict.get("CLAVE DE LA INSTITUCION")
        name_inst = row_dict.get("NOMBRE DE LA INSTITUCION")
        if clave_inst not in self.new_institutions_names:
            self.new_institutions_names[clave_inst] = name_inst

        institution_id = self.institution_dict.get(clave_inst)
        if not institution_id:
            # self.stdout.write(
            #     self.style.ERROR(
            #         f"Error saving clues {clues_key}: "
            #         f"Institution {clave_inst} not found"))
            if clave_inst not in self.geo_errors["institution"]:
                self.geo_errors["institution"].append(clave_inst)
            return

        try:
            clues = CLUES.objects.get(clues=clues_key)
            clues.institution_id = institution_id
            return clues

        except CLUES.DoesNotExist:
            clues = CLUES()

        clues.clues = clues_key
        clues.institution_id = institution_id

        clave_ent = row_dict.get("CLAVE DE LA ENTIDAD")
        clave_mun = f"{clave_ent}-{row_dict.get('CLAVE DEL MUNICIPIO')}"

        clues.state_id = self.state_dict.get(clave_ent)
        if not clues.state_id:
            # self.stdout.write(
            #     self.style.ERROR(
            #         f"Error saving clues {clues_key}: "
            #         f"State {clave_ent} not found"))
            if clave_ent not in self.geo_errors["state"]:
                self.geo_errors["state"].append(clave_ent)
            return

        clues.municipality_id = self.municipality_dict.get(clave_mun)

        return clues

    def check_equivalences(self, headers: List[str]):

        self.stdout.write(self.style.SUCCESS("Checking equivalences..."))

        all_check_fields = True

        for xls_field, _ in equivalences:
            if xls_field not in headers:
                self.stdout.write(
                    self.style.ERROR(f"equivalences Field {xls_field} not found in the headers"))
                all_check_fields = False

        for xls_field, _ in integers_equivalences:
            if xls_field not in headers:
                self.stdout.write(
                    self.style.ERROR(f"integers_equivalences Field {xls_field} not found in the headers"))
                all_check_fields = False

        for field in self.sum_fields:
            for f in self.sum_fields[field]:
                if f not in headers:
                    self.stdout.write(
                        self.style.ERROR(f"sum_fields Field {f} not found in the headers"))
                    all_check_fields = False

        for field in self.concat_fields:
            for f in self.concat_fields[field]:
                if f not in headers:
                    self.stdout.write(
                        self.style.ERROR(f"concat_fields Field {f} not found in the headers"))
                    all_check_fields = False

        if not all_check_fields:
            self.stdout.write(self.style.ERROR("Some fields are missing"))
        else:
            self.stdout.write(self.style.SUCCESS("All fields are present"))

        return all_check_fields

    def update_institutions_names(self):
        for clave_inst, name_inst in self.new_institutions_names.items():
            inst_id = self.institution_dict.get(clave_inst)
            Institution.objects.filter(id=inst_id).update(name=name_inst)
