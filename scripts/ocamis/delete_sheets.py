from django.db import connection
from task.aws.common import calculate_delivered_final
from datetime import datetime
from respond.models import DataFile, SheetFile


def delete_sheet_file(uuid_folios):
    print("start delete_folios", datetime.now())
    cursor = connection.cursor()
    sql_delete_pres = f"""
        DELETE FROM formula_rx rx
        WHERE rx.uuid_folio IN ({uuid_folios})
    """
    cursor.execute(sql_delete_pres)
    sql_delete_drug = f"""
        DELETE FROM formula_drug drug
        WHERE drug.rx_id IN ({uuid_folios})
    """
    cursor.execute(sql_delete_drug)
    cursor.close()


def get_only_uuids(sheet_file_id):
    sql_query = f"""
        SELECT
            uuid_folio,
        FROM
            drugs_and_rxs
        WHERE
            sheet_id = {sheet_file_id}
    """
    cursor = connection.cursor()
    cursor.execute(sql_query)
    while True:
        current_uuids = cursor.fetchmany(50000)
        if not current_uuids:
            break
        only_uuids = ", ".join([f"'{uuid}'" for uuid in current_uuids])
        delete_sheet_file(only_uuids)
    cursor.close()


def delete_data_file(data_file_id):
    data_file = DataFile.objects.get(id=data_file_id)
    sheet_files = data_file.sheet_files.all()
    for sheet_file in sheet_files:
        sheet_file.delete()

