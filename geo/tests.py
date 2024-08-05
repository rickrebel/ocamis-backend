from django.test import TestCase
from django.contrib.auth.models import User

# Create your tests here.


class TestLoadCatalog(TestCase):
    # Carga de fixtures en este orden para evitar problemas de integridad referencial
    fixtures = [
        "fixture/db/auth_user.json",
        # "fixture/db/med_cat.json",
        # "fixture/db/respond.json",
        # "fixture/db/category.json",
        # "fixture/db/geo.json",
        # "fixture/db/classify_task.json",
        # "fixture/db/data_param.json",
        # "fixture/db/medicine.json",
        # "fixture/db/transparency.json",
        # "fixture/db/rds.json",

    ]

    def test_load_catalog(self):
        self.assertTrue(User.objects.all().count() > 0)
        User.objects.all().delete()
    
    def test_load_catalog2(self):
        # los datos no son persistentes, se reinician en cada test
        self.assertTrue(User.objects.all().count() > 0)
        User.objects.all().delete()
