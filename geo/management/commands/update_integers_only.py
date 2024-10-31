import pandas as pd
from pandas import DataFrame
from django.core.management.base import BaseCommand

from geo.models import CLUES


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
        sheet_name = options["sheet_name"] or "CLUES_ENERO_2023"

        if not file_path:
            raise ValueError("File path not provided")

        self.integers_equivalences = [
            ("CONSULTORIOS DE MED GRAL", "consultings_general"),
            ("CONSULTORIOS EN OTRAS AREAS", "consultings_other"),
            ("CAMAS EN AREA DE HOS", "beds_hopital"),
            ("CAMAS EN OTRAS AREAS", "beds_other"),
        ]
        self.sum_fields = {
            "total_unities": [
                "CONSULTORIOS DE MED GRAL",
                "CONSULTORIOS EN OTRAS AREAS",
                "CAMAS EN AREA DE HOS",
                "CAMAS EN OTRAS AREAS",
            ],
        }

        self.stdout.write(self.style.SUCCESS("Reading excel file..."))

        excel_file = pd.ExcelFile(file_path)
        data_excel = excel_file.parse(
            sheet_name, dtype="string", na_filter=False, keep_default_na=False
        )

        for _, row in data_excel.iterrows():
            row_dict = row.to_dict()
            self.match_data(row_dict)

    def match_data(self, row_dict: dict):
        clues_key = row_dict.get("CLUES")
        try:
            clues = CLUES.objects.get(clues=clues_key)
        except CLUES.DoesNotExist:
            return

        for xls_field, model_field in self.integers_equivalences:
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

        try:
            clues.save()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error saving clues {clues_key}: {e}"))
