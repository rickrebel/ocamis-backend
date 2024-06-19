import gzip
import shutil
# import os
from django.conf import settings

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def csv_to_gz(csv_filepath, gz_filepath):
    try:
        with open(csv_filepath, 'rb') as f_in:
            with gzip.open(gz_filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print(e)


def transform_gz(file_name):
    base_dir = settings.BASE_DIR
    origin_path = f"{base_dir}\\fixture\\gz_files\\{file_name}"
    final_path = f"{base_dir}\\fixture\\gz_files\\{file_name}.gz"

    csv_to_gz(origin_path, final_path)


transform_gz("2017_chih.txt")

# february_files = [
#     "Febrero 2022-Chihuahua.xlsx",
#     "Febrero 2022-Coahuila.xlsx",
#     "Febrero 2022-Baja California Norte.xlsx",
# ]

# january_files = [
#     "Enero 2022-Chihuahua.xlsx",
#     "Enero 2022-Coahuila.xlsx",
#     "Enero 2022-Guanajuato.xlsx",
#     "Enero 2022-Jalisco.xlsx",
#     "Enero 2022-Nuevo Leon.xlsx",
#     "Enero 2022-Sinaloa.xlsx",
#     "Enero 2022-DF Norte.xlsx",
#     "Enero 2022-DF Sur.xlsx",
#     "Enero 2022-Mexico Oriente.xlsx",
#     "Enero 2022-Mexico Poniente.xlsx",
# ]
#
# for file_name in january_files:
#     simple_name = file_name.split(".")[0]
#     for x in range(1, 4):
#         print(x)
#         csv_name = f"{simple_name}_Hoja_{x}.csv"
#         transform_gz(csv_name)

regions = [
    'Norte.xlsx',
    'Occidente.xlsx',
    'Centro.xlsx',
    'Sur.xlsx'
]
for region in regions:
    for x in range(1, 7):
        print(x)
        simple_name = region.split(".")[0]
        csv_name = f"{simple_name}_{simple_name}_{x}.csv"
        transform_gz(csv_name)
        csv_name2 = f"{simple_name}_{simple_name}_{x} (2).csv"
        transform_gz(csv_name2)
