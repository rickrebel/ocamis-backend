"""
cd /var/www/ocamis/
. /home/ubuntu/env/desabasto/bin/activate
python manage.py shell

"""

import csv
import json
from urllib.parse import unquote

from scripts.common import build_s3
from task.aws.common import BotoUtils


TOTAL_ROWS = 941533

FILTER_DIRECTORIES = [
    'data_files/data/',
    'data_files/estatal/',
    'data_files/hospital/',
    'data_files/mat_views/',
    'data_files/merged_tables/',
    'data_files/month_tables/',
    'data_files/nacional/',
    'data_files/reply/',
    'data_files/sheet/',
    'data_files/sin_instance/',
    'data_files/table/'
]



def change_storage_class(start_index=0, limit=100, post_fij=''):
    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)
    change_list = []
    last_row_index = - 1
    errors_files = []
    try:
        with open('s3_storage_files.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                last_row_index += 1
                if last_row_index < start_index:
                    # print(f'Skipping row {last_row_index}')
                    continue
                if last_row_index > start_index + limit:
                    break
                bucket = row[0]
                path_file = row[1]

                path_file = unquote(path_file)

                if path_file[-1] == '/':
                    # print(f'ignoring directory {path_file}')
                    continue
                if not any(path_file.startswith(directory) for directory in FILTER_DIRECTORIES):
                    # print(f'ignoring file {path_file} not in directories')
                    continue
                if len(row) > 4 and row[4] == 'STANDARD':
                    # quitar data_files/ del inicio del path
                    path_file_ = path_file[11:]
                    print(
                        f'Row {last_row_index}/{TOTAL_ROWS} {path_file_} {row}')
                    try:
                        s3_utils.change_storage_class(
                            path_file_, 'DEEP_ARCHIVE')
                    except Exception as e:
                        print(f'Error en la fila {last_row_index}')
                        print(e)
                        errors_files.append([row, str(e)])
                    change_list.append([bucket, path_file_])
                else:
                    # print(f'ignoring file {row} not in STANDARD storage class')
                    continue
    except Exception as e:
        print(f'Error en la fila {last_row_index}')
        print(e)
    with open(f'change_storage_class{post_fij}.json', 'w', encoding='utf-8') as file:
        json.dump(change_list, file, indent=4)
    with open(f'errors_files{post_fij}.json', 'w', encoding='utf-8') as file:
        json.dump(errors_files, file, indent=4)


change_storage_class(0, limit=100000, post_fij="_0")
change_storage_class(100000, limit=100000, post_fij="_100000")
change_storage_class(200000, limit=100000, post_fij="_200000")
change_storage_class(300000, limit=100000, post_fij="_300000")
change_storage_class(400000, limit=100000, post_fij="_400000")
change_storage_class(500000, limit=100000, post_fij="_500000")
change_storage_class(600000, limit=100000, post_fij="_600000")
change_storage_class(700000, limit=100000, post_fij="_700000")
change_storage_class(800000, limit=100000, post_fij="_800000")
change_storage_class(900000, limit=100000, post_fij="_900000")
change_storage_class(1000000, limit=100000, post_fij="_1000000")


