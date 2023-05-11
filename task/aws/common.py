request_headers = {"Content-Type": "application/json"}


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


def calculate_delivered_final(all_delivered, all_write=None):
    error = None
    if all_write:
        if len(all_write) > 1:
            error = f"Hay más de una clasificación de surtimiento;" \
                    f" {list(all_write)}"

    if len(all_delivered) == 1:
        return all_delivered.pop(), error
    if "partial" in all_delivered:
        return "partial", error
    has_complete = "complete" in all_delivered
    has_over = "over_delivered" in all_delivered
    has_denied = "denied" in all_delivered
    has_cancelled = "cancelled" in all_delivered
    if (has_complete or has_over) and (has_denied or has_cancelled):
        return "partial", error
    initial_list = all_delivered.copy()
    if "zero" in all_delivered:
        all_delivered.remove("zero")
    if has_over and has_complete:
        all_delivered.remove("complete")
    if has_denied and has_cancelled:
        all_delivered.remove("denied")
    if len(all_delivered) == 1:
        return all_delivered.pop(), error
    return "unknown", f"No se puede determinar el status de entrega; " \
                      f"{list(initial_list)}"
