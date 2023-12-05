
from django.conf import settings


def local_xls_to_csv(folder_path, file_name):
    import pandas as pd
    import io
    import csv

    xls_filepath = f"{folder_path}\\{file_name}"
    excel_file = pd.ExcelFile(xls_filepath)
    all_sheet_names = excel_file.sheet_names
    for sheet_name in all_sheet_names:
        data_excel = excel_file.parse(
            sheet_name,
            dtype='string', na_filter=False,
            keep_default_na=False, header=None)
        data_excel = data_excel.replace(
            to_replace=[r"\\t|\\n|\\r", "\t|\n|\r", "\|"],
            value=[" > ", " > ", ";"],
            regex=True)
        csv_buffer = io.StringIO()
        data_excel.to_csv(
            csv_buffer, index=False, header=False, sep="|", escapechar="\\")
        # save in local
        csv_filepath = f"{folder_path}\\csv\\{file_name.split('.')[0]}"
        new_csv_filepath = f"{csv_filepath}_{sheet_name}.csv"
        with open(new_csv_filepath, 'w', newline='') as f:
            f.write(csv_buffer.getvalue())
        # if alternative:
        #     with open(new_csv_filepath, 'w', newline='') as csvfile:
        #         writer = csv.writer(csvfile, delimiter='|')
        #         writer.writerows(csv_buffer.getvalue())
        # else:


def execute_local_xls_to_csv(file_name):
    # import os
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = settings.BASE_DIR
    # file_name = "Febrero 2022-Sonora.xlsx"
    # file_name = "Febrero 2022-Especialidades Jalisco.xlsx"
    # file_name = "Febrero 2022-Especialidades Jalisco.xlsx"
    folder_path = f"{base_dir}\\fixture\\large_xls"
    origin_path = f"{base_dir}\\fixture\\large_xls\\{file_name}"
    simple_file_name = file_name.split(".")[0]
    final_path = f"{base_dir}\\fixture\\large_xls\\{simple_file_name}"

    local_xls_to_csv(folder_path, file_name)

    # from task.aws.common import BotoUtils
    # from scripts.common import start_session, create_file
    # aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    # aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    # s3 = {
    #     "aws_access_key_id": aws_access_key_id,
    #     "aws_secret_access_key": aws_secret_access_key,
    #     "bucket_name": getattr(settings, "AWS_STORAGE_BUCKET_NAME"),
    #     "aws_location": getattr(settings, "AWS_LOCATION"),
    # }

    # s3_client, dev_resource = start_session()
    # event = event()
    # s3_utils = BotoUtils(s3)
    # final_name = f"{only_name}_SHEET_{sheet_name}.csv"
    # s3_utils.save_file_in_aws(csv_buffer.getvalue(), final_name)


# execute_local_xls_to_csv("Febrero 2022-Zacatecas.xlsx")
# execute_local_xls_to_csv("Febrero 2022-Sonora.xlsx")
# execute_local_xls_to_csv("Febrero 2022-Especialidades Jalisco.xlsx")
#
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
# for file_name in january_files:
#     execute_local_xls_to_csv(file_name)

february_files = [
    "Febrero 2022-Chihuahua.xlsx",
    "Febrero 2022-Coahuila.xlsx",
    "Febrero 2022-Baja California Norte.xlsx",
]

for file_name in february_files:
    execute_local_xls_to_csv(file_name)
