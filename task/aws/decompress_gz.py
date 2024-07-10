from task.aws.common import (obtain_decode, send_simple_response, BotoUtils,
                             calculate_delimiter, decode_content)


# def decompress_gz(event, context):
def lambda_handler(event, context):

    decompress_gz = DecompressGz(event, context)
    file = event["file"]
    result, errors = decompress_gz.decompress(file)

    return send_simple_response(event, context, errors, result)


class DecompressGz:

    def __init__(self, event: dict, context):
        self.context = context
        self.s3_utils = BotoUtils(event["s3"])
        self.delimiter = event.get("delimiter")
        self.decode = event.get("decode")
        self.directory = event["directory"]

    def decompress(self, file):
        import gzip
        decompressed_path = file.replace(".gz", "")
        pos_slash = decompressed_path.rfind("/")
        only_name = decompressed_path[pos_slash + 1:]
        is_gz = file.endswith(".gz")
        file_type = "gz" if is_gz else "csv"

        file_obj = self.s3_utils.get_object_file(file, file_type)

        if is_gz:
            with gzip.GzipFile(fileobj=file_obj) as gzip_file:
                result, errors = self.write_split_files(gzip_file, only_name)
        else:
            with file_obj.get()['Body'] as csv_file:
                result, errors = self.write_split_files(csv_file, only_name)
        result["matched"] = True
        result["file_type_id"] = "split"
        errors += self.s3_utils.errors
        return result, errors

    def write_split_files(self, complete_file, simple_name):
        import math
        import json

        [base_name, extension] = simple_name.rsplit(".", 1)
        file_num = 0
        new_files = []
        errors = []
        # header_validated = []
        # tail_validated = []
        size_hint = 300 * 1000000
        has_cut = False
        cut_lap = 0
        print("size_hint", size_hint)

        while True and not errors:
            if has_cut:
                size_hint = int(math.ceil(size_hint / 2))
                cut_lap += 1
            if cut_lap > 7:
                break

            try:
                buf = complete_file.readlines(size_hint)
            except Exception as e:
                print("Error reading file", e)
                has_cut = True
                continue

            if not buf:
                print("No hay más datos")
                break

            # if not header_validated:
            header_data = buf[:220]
            tail_data = buf[-50:]

            if not self.decode:
                self.decode = obtain_decode(header_data)
                if self.decode == "unknown":
                    errors.append("No se pudo decodificar el archivo")
            sample_header = decode_content(header_data, self.decode)
            sample_tail = decode_content(tail_data, self.decode)
            if not self.delimiter:
                self.delimiter = calculate_delimiter(sample_header)
            if errors:
                break

            header_validated = self.divide_rows(sample_header)
            tail_validated = self.divide_rows(sample_tail)
            split_sample = {
                "all_data": header_validated,
                "tail_data": tail_validated,
            }
            split_sample = json.dumps(split_sample)

            file_num += 1
            curr_only_name = f"{base_name}_{file_num}.{extension}"
            curr_only_name = self.directory.replace(
                "NEW_FILE_NAME", curr_only_name)
            curr_sample_name = f"sample_{file_num}_sample.json"
            curr_sample_name = self.directory.replace(
                "NEW_FILE_NAME", curr_sample_name)

            self.s3_utils.save_file_in_aws(split_sample, curr_sample_name)

            total_rows = len(buf)
            buf = b"".join(buf)
            # print("len buf", len(buf))
            # print("rr_file_name", curr_only_name)
            self.s3_utils.save_file_in_aws(buf, curr_only_name)
            current_file = {
                "total_rows": total_rows,
                "final_path": curr_only_name,
                "sheet_name": file_num,
                "sample_path": curr_sample_name,
            }
            new_files.append(current_file)
            # complete_file.seek(0, 1)

        result = {
            "new_files": new_files,
            "decode": self.decode,
            "delimiter": self.delimiter,
            # "all_data": header_validated,
            # "tail_data": tail_validated,
        }

        return result, errors

    def divide_rows(self, data_rows):
        # print("DIVIDE_ROWS", data_rows)
        structured_data = []
        for row_seq, row in enumerate(data_rows, 1):
            # print("\n")
            row_data = row.split(self.delimiter)
            row_data = [x.strip() for x in row_data]
            structured_data.append(row_data)
        return structured_data
