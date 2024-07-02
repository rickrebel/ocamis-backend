
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
    # file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/UMAE_PEDIATRIA_SXXI_enero_2021.pdf"
    file_path = "fixture/especiales/UMAE_TRAUMA_PUEBLA_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    pdf = fitz.open(file_path)
    print(pdf.page_count)
    for i in range(pdf.page_count):
        page = pdf[i]
        text = page.get_text("text", flags=fitz.TEXT_INHIBIT_SPACES)
        print(text)


def simple_decode_char(char):
    cid = ord(char)

    if cid == 0:
        return '*'
    if cid == 10:
        return '\n'
    elif cid == 98:
        return ' '
    elif 3 <= cid <= 95:
        return chr(cid + 29)

    return f'(cid:{cid}:{chr(cid + 29)})'


def read_with_pypdf2():
    import PyPDF2
    import codecs
    import chardet
    from django.utils import timezone
    from pdfminer.pdffont import PDFCIDFont
    # file_path = "fixture/especiales/UMAE_GIN_NUEVO_LEON_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "H:\\Mi unidad\\IMSS\\2023-5\\JAL_REQ_2023006432_JULIO_2023.pdf"
    # file_path = "fixture/especiales/330018021009264.pdf"
    # file_path = "fixture/especiales/UMAE_PEDIATRIA_SXXI_enero_2021.pdf"
    # file_path = "fixture/especiales/QROO_REQ_18023022639_MAYO_2023.pdf"
    # file_path = "fixture/especiales/UMAE_TRAUMA_PUEBLA_REQ_18023022639_MAYO_2023.pdf"
    file_path = "fixture/especiales/YUCATAN_febrero_2021.pdf"
    print("Start at:", timezone.now())
    pdf = PyPDF2.PdfReader(stream=file_path)
    print(len(pdf.pages))
    final_text = ''
    # for page in pdf.pages:
    #     text = page.extractText()
    #     for char in text:
    #         final_char = simple_decode_char(char)
    #         final_text += final_char
    #     # print("text", text)
    #     # text_in_bytes = current_page.extractText().encode('ascii', 'ignore')
    #     # text_in_bytes2 = first_page.extractText().encode('utf-8', 'ignore')
    #     # text_in_utf8 = text_in_bytes.decode('utf-8')
    #     # res = chardet.detect(text_in_bytes)
    #     # print(res)
    #     # print("----"*10)
    #     # print(text_in_bytes)
    print("End at:", timezone.now())

    first_page = pdf.pages[0]
    text = first_page.extractText()
    font = PDFCIDFont(None, first_page)
    print("font", font)
    # print("text", text)
    new_text = ''
    for char in text:
        final_char = simple_decode_char(char)
        # print("char", char, ord(char), final_char)
        new_text += final_char
    # print("new_text", new_text)
    text_in_bytes = first_page.extractText().encode('ascii', 'ignore')
    # text_in_bytes2 = first_page.extractText().encode('utf-8', 'ignore')
    # text_in_utf8 = text_in_bytes.decode('utf-8')
    # res = chardet.detect(text_in_bytes)
    # print(res)
    print("----"*10)
    print(text_in_bytes)
    # print("----"*10)
    # print(text_in_bytes2)
    # print("----"*10)
    # print(text_in_utf8)


def read_with_slate():
    from slate3k import PDF
    import slate3k as slate
