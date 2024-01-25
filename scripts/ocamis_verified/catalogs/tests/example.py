
from scripts.ocamis_verified.catalogs.compendio import ProcessPDF
from scripts.ocamis_verified.catalogs.compendio2 import (
    BuildNewTable, get_pdf_data, file_path)


# get_pdf_data()


table = BuildNewTable()
table()

table.save_csv()


pdf = ProcessPDF(file_path)
pdf(pages_range=[671, 673])

pdf.first_page


# 010.000.6282.00





# 040.000.2500.00
# 010.000.6276.00
# 010.000.6251.00


# VACUNA TRIPLE VIRAL (SRP ) CONTRA SARAMPIÓN, RUBÉOLA Y PAROTIDITIS
