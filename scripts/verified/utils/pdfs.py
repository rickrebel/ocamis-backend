
def read_pdf_table():
    import camelot
    file_path = "fixture/especiales/UMAE_TRAUMA_PUEBLA_REQ_18023022639_MAYO_2023.pdf"
    abc = camelot.read_pdf(file_path, pages="all")
    print(abc[0].df)


def read_with_plumber():
    import pdfplumber
    file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        print(first_page.extract_text())


def read_with_pdfminer():
    from pdfminer.high_level import extract_text
    file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    text = extract_text(file_path)
    print(text)


def coding_and_read_with_pdfminer(font='DejaVu Sans'):
    from pdfminer.layout import LAParams
    from pdfminer.high_level import extract_text_to_fp
    import io

    file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    output_string = io.StringIO()
    with open(file_path, 'rb') as f:
        extract_text_to_fp(f, output_string, laparams=LAParams(), output_type='text', codec=None)


# # BUENOS

def read_with_pymupdf(font='DejaVu Sans'):
    import fitz
    file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    pdf = fitz.open(file_path)
    print(pdf.page_count)
    first_page = pdf[0]
    text = first_page.get_text("text", flags=fitz.TEXT_INHIBIT_SPACES)
    print(text)


def read_with_pypdf2():
    import PyPDF2
    import codecs
    import chardet
    file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "H:\\Mi unidad\\IMSS\\2023-5\\JAL_REQ_2023006432_JULIO_2023.pdf"
    # file_path = "H:\\Mi unidad\\IMSS\\2023-7\\UMAE_ESP_RAZA_REQ_2023006432_AGOSTO_2023.pdf"
    # file_path = "H:\\Mi unidad\\IMSS\\2023-5\\UMAE_TRAUMA_PUEBLA_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    with open(file_path, "rb") as file:
        pdf = PyPDF2.PdfFileReader(file)
        print(pdf.numPages)
        first_page = pdf.getPage(0)
        text = first_page.extractText()
        print("text")
        text_in_bytes = first_page.extractText().encode('ascii', 'ignore')
        text_in_bytes2 = first_page.extractText().encode('utf-8', 'ignore')
        text_in_utf8 = text_in_bytes.decode('utf-8')
        # res = chardet.detect(text_in_bytes)
        # print(res)
        print("----"*10)
        print(text_in_bytes)
        print("----"*10)
        print(text_in_bytes2)
        print("----"*10)
        print(text_in_utf8)


