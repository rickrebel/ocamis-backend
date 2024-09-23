from task.aws.common import (obtain_decode, send_simple_response, BotoUtils,
                             calculate_delimiter, decode_content)


# def compress_gz(event, context):
def lambda_handler(event, context):

    gz = CompressGz(event, context)
    file = event["file"]
    result, errors = gz.compress_gz(file)

    return send_simple_response(event, context, errors, result)


class CompressGz:

    def __init__(self, event: dict, context):
        self.context = context
        self.s3_utils = BotoUtils(event["s3"])

    def compress_gz(self, file):
        import gzip
        from io import BytesIO

        errors = []

        compressed_path = f"{file}.gz"
        file_bytes = self.s3_utils.get_object_file(file, "csv_to_gz")

        gz_buffer = BytesIO()
        with gzip.GzipFile(mode='wb', fileobj=gz_buffer) as gz_file:
            gz_file.write(file_bytes)
        self.s3_utils.save_file_in_aws(
            gz_buffer.getvalue(), compressed_path,
            content_type="application/gzip")
        errors += self.s3_utils.errors
        result = {"new_path": compressed_path}
        return result, errors


