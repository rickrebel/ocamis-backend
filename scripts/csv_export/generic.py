
import csv
from datetime import datetime, date
from decimal import Decimal


def to_csv_friendly(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    else:
        return str(value)


class CsvExporter:
    def __init__(self, query, headers, attributes, file_path):
        self.query = query
        self.headers = headers
        self.attributes = attributes
        self.file_path = file_path

    def verify_data_integrity(self):
        if not self.attributes:
            return
        if len(self.headers) != len(self.attributes):
            raise ValueError(
                "Las listas de cabezales y atributos deben tener el mismo tamaño")

    def write_headers(self, writer):
        writer.writerow(self.headers)

    def write_rows(self, writer):
        for obj in self.query:
            if isinstance(obj, list):
                row = [to_csv_friendly(attr) for attr in obj]
            elif isinstance(obj, dict):
                row = [to_csv_friendly(obj.get(attr, ""))
                       for attr in self.attributes]
            else:
                row = [to_csv_friendly(getattr(obj, attr, ""))
                       for attr in self.attributes]
            writer.writerow(row)

    def generate_csv(self):
        self.verify_data_integrity()
        with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            self.write_headers(writer)
            self.write_rows(writer)
        return self.file_path
