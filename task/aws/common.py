
def calculate_delimiter(data):
    error_count = 0
    for row in data:
        try:
            if "|" in row:
                return "|"
        except Exception as e:
            error_count += 1
            if error_count > 3:
                print("row:\n", row)
                print("error", e)
                if "|" in row:
                    return "|"
    return ","


def obtain_decode(sample):
    for row in sample:
        is_byte = isinstance(row, bytes)
        posible_latin = False
        if is_byte:
            try:
                row.decode("utf-8")
            except Exception:
                posible_latin = True
            if posible_latin:
                try:
                    row.decode("latin-1")
                    return "latin-1"
                except Exception as e:
                    print(e)
                    return "unknown"
        else:
            return "str"
    return "utf-8"


def decode_content(data_rows, decode):
    decoded_data = []
    for row in data_rows:
        content = str(row) if decode == 'str' else row.decode(decode)
        decoded_data.append(content)
    return decoded_data
