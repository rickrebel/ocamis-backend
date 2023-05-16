import gzip
import shutil
import os
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

base_dir = settings.BASE_DIR
file_name = "recetas_201703TESTING.csv"
origin_path = f"{base_dir}\\fixture\\gz_files\\{file_name}"
final_path = f"{base_dir}\\fixture\\gz_files\\{file_name}.gz"


def csv_to_gz(csv_filepath, gz_filepath):
    with open(csv_filepath, 'rb') as f_in:
        with gzip.open(gz_filepath, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


csv_to_gz(origin_path, final_path)
