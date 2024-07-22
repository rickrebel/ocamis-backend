from django.test import TestCase
from django.contrib.auth.models import User

# Create your tests here.


class TestLoadCatalog(TestCase):
    # Carga de fixtures en este orden para evitar problemas de integridad referencial
    fixtures = [
        "fixtures/auth_user.json",
        # "fixtures/med_cat.json",
        # "fixtures/respond.json",
        # "fixtures/category.json",
        # "fixtures/geo.json",
        # "fixtures/classify_task.json",
        # "fixtures/data_param.json",
        # "fixtures/medicine.json",
        # "fixtures/transparency.json",
        # "fixtures/rds.json",

    ]

    def test_load_catalog(self):
        self.assertTrue(User.objects.all().count() > 0)
        User.objects.all().delete()
    
    def test_load_catalog2(self):
        # los datos no son persistentes, se reinician en cada test
        self.assertTrue(User.objects.all().count() > 0)
        User.objects.all().delete()
