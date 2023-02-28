
def special_coma(all_data):
    rows = all_data.split("\n")
    count = 0
    final_rows = []
    for idx, row in enumerate(rows):
        new_row = row.replace('1,114 gr.', '1$114 gr.')\
            .replace('0,000', '0$000').replace('VERACRUZ,VER', 'VERACRUZ$VER')\
            .replace(' VEGA,CULIAC', 'VEGA$CULIAC')\
            .replace(' PUCHADES,TEPIC', 'PUCHADES$TEPIC')
        cols = new_row.split(",")
        len_cols = len(cols)
        if len_cols == 17:
            final_rows.append(sep_cols.join(cols).replace('$', ","))
        elif len_cols > 17:
            new_row = new_row.replace(
                ',',
                '|').replace(
                '| ',
                ', ').replace(
                '$',
                ",")
            cols = new_row.split(sep_cols)
            len_cols = len(cols)
            if len_cols == 16:
                clave = cols[13].replace(', ', ',').split(",")
                cols = sep_cols.join(cols[:13] + clave + cols[14:])
                final_rows.append(cols)
            elif len_cols == 17:
                final_rows.append(new_row)
            elif len_cols > 17:
                count += 1
                if count < 20:
                    print("--------------------")
                    print("error 1")
                    print(idx)
                    print(row)
                    # break
                # print (new_row)
                # for col in cols:
                #    print (col)
            else:
                count += 1
                print("error 2")
                print(row)
                # break
        else:
            print("error 3")
            print(row)
            break
    print("especial coma %s errores" % count)
    all_data = sep_rows.join(final_rows)
    return all_data


def clean_special(data):
    message_final = 'sys.databases\n'
    idx_col = 0
    while True:
        try:
            idx_col = data.index('COLECTIVO|', idx_col + 80)
            idx_year = data.index("|%s" % year, idx_col, idx_col + 80)
            if "|" in data[idx_col + 10:idx_year]:
                print("hay un espacio de mas")
                curr_str = data[idx_col + 10:idx_year - 1]
                print(curr_str)
                curr_done = curr_str.replace("|", "-")
                next_data = data[idx_col:idx_col + 6000]
                cleaned_current = next_data.replace(curr_str, curr_done)
                data = "%s%s%s" % (
                    data[:idx_col], cleaned_current, data[idx_col + 6000:])
            else:
                pass
        except Exception:
            break
    while True:
        try:
            idx_msg = data.index('Mensaje 9002')
            idx_msg2 = data.index(message_final, idx_msg)
            print("----------")
            print(data[idx_msg:idx_msg2 + len(message_final)])
            data = "%s%s" % (data[:idx_msg],
                             data[idx_msg2 + len(message_final):])
        except Exception:
            break
    fabian = 'FABIAN ZARATE GALINDO|'
    fabian2 = 'FABIAN ZARATE GALINDO||'
    if fabian2 in data:
        print("caso FABIAN")
        data = data.replace(fabian2, fabian)
    return data


def special_excel(all_data):
    import re
    rows = all_data.split("\n")
    final_rows = []
    for row in rows:
        new_row = re.sub(r'(\,)+$', r'', row)
        final_rows.append(new_row)
    all_data = sep_rows.join(final_rows)
    return all_data


def special_issste(data, file_control, is_issste):
    if "|" in data[:5000]:
        file_control.delimiter = '|'
    elif "," in data[:5000]:
        file_control.delimiter = ','
        if is_issste:
            data = special_coma(data)
            if ",,," in data[:5000]:
                data = special_excel(data)
    #elif not set([',', '|']).issubset(data[:5000]):
    else:
        return [], ['El documento está vacío'], None
    file_control.save()
    if is_issste:
        data = clean_special(data)
    return [], [], data
