import json
import random
from datetime import datetime
from django.test import TestCase
from category.models import ColumnType
from data_param.models import NameColumn, FileControl, DataType, FinalField
from respond.models import DataFile
from inai.models import Petition
from scripts.common import similar, text_normalizer
from geo.models import Agency, Provider


class Request:
    user = None

    def __init__(self, file_id):
        self.query_params = {"file_id": file_id}


class NameColumnTestCase(TestCase):

    def setUp(self):
        self.column_original = ColumnType.objects.get(name="original_column")
        self.provider = Provider.objects.create(
            name="Provider Test 1",
            acronym="PT1",
            short_name="PT1",
        )
        self.first_agency = Agency.objects.create(
            name="Agency1",
            provider=self.provider,
            acronym="A1",
            is_pilot=True)
        self.file_format = FileControl.objects.get(short_name="xls")
        self.file_control = FileControl.objects.create(
            name="Test 1",
            data_group_id="detailed",
            agency=self.first_agency,
            file_format=self.file_format,
            row_headers=3,
            row_start_data=4,
            status_register_id="initial_register",
        )
        self.data_type_char = DataType.objects.get(name="Char")
        self.data_type_date = DataType.objects.get(name="Datetime")
        self.data_type_int = DataType.objects.get(name="Integer")
        self.final_field = FinalField.objects.create(name="FinalField1")

    # el más simple, sin transformaciones ni nada
    def test_file_control_creation(self):
        from inai.api.views_aws import AutoExplorePetitionViewSet

        names_columns = [
             {
                 "name_in_data": "",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Others", "*empty"),
             },
             {
                 "name_in_data": "Unidad Médica",
                 "data_type": self.data_type_char,
                 "final_field_data": ("MedicalUnit", "name"),
             },
             {
                 "name_in_data": "Clave CLUES",
                 "data_type": self.data_type_char,
                 "final_field_data": ("MedicalUnit", "clues_key"),
             },
             {
                 "name_in_data": "Clave artículo",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Medicament", "key2"),
             },
             {
                 "name_in_data": "Nombre artículo",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Medicament", "component_name"),
             },
             {
                 "name_in_data": "Fecha de emisión",
                 "data_type": self.data_type_date,
                 "final_field_data": ("Rx", "date_visit"),
             },
             {
                 "name_in_data": "Clave diagnóstico",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Diagnosis", "cie10"),
             },
             {
                 "name_in_data": "Diagnóstico",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Diagnosis", "text"),
             },
             {
                 "name_in_data": "Fecha de entrega",
                 "data_type": self.data_type_date,
                 "final_field_data": ("Rx", "date_delivery"),
             },
             {
                 "name_in_data": "Cantidad prescrita",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Drug", "prescribed_amount"),
             },
             {
                 "name_in_data": "Cantidad entregada",
                 "data_type": self.data_type_char,
                 "final_field_data": ("Drug", "delivered_amount"),
             }
        ]
        for (idx, name_col_data) in enumerate(names_columns, start=1):
            collection, field_name = name_col_data["final_field_data"]
            final_field = FinalField.objects.get(
                collection__name=collection, field=field_name)
            name_col_data["position_in_file"] = idx
            name_col_data["seq"] = idx
            name_col_data["final_field"] = final_field
            name_col_data["file_control"] = self.file_control
            name_col_data["column_type"] = self.column_original
            std_name = text_normalizer(name_col_data["name_in_data"], True)
            name_col_data["std_name_in_data"] = std_name
            name_column = NameColumn.objects.create(**name_col_data)

        # Subir el xls a S3 manualmente

        # CREAR LA SOLICITUD (Petition)
        new_petition = Petition.objects.create(
            agency=self.first_agency,
            provider=self.provider,
            name="Petition Test 1",
        )

        data_file = DataFile.objects.create(
            file="s3/test_file.xls",
            provider=self.provider,
            file_control=self.file_control,
        )

        request = Request(data_file.id)

        class NewAutoExplorePetitionViewSet(AutoExplorePetitionViewSet):
            def get_object(self):
                return new_petition

        view = NewAutoExplorePetitionViewSet()
        view.data_file(request)


        # get a auto_explore/data_file con el file_id



