import io
from task.aws.common import send_simple_response, BotoUtils


# def split_horizontal(event, context):
def lambda_handler(event, context):
    import traceback

    try:
        init_data = event["init_data"]
        split_aws = SplitAws(init_data, context, event.get("s3"))
    except Exception as e:
        errors = [f"Hay Un error raro en la inicialización: {str(e)}"]
        return send_simple_response(event, context, errors=errors)

    try:
        file = event["file"]
        final_result = split_aws.split_horizontal(file)
    except Exception as e:
        error_ = traceback.format_exc()
        errors = [f"Hay un error raro en la construcción: \n{str(e)}\n{error_}"]
        return send_simple_response(event, context, errors=errors)

    return send_simple_response(event, context, result=final_result)


class SplitAws:

    def __init__(self, init_data: dict, context, s3):
        self.final_path = ""
        for key, value in init_data.items():
            setattr(self, key, value)
        self.destinations = []

        self.s3_utils = BotoUtils(s3)
        self.context = context

    def split_horizontal(self, csv_file):
        import pandas as pd
        csv_content = self.s3_utils.get_object_file(csv_file, file_type="nada")

        df = pd.read_csv(csv_content, delimiter="|", escapechar="\\")
        # only_name = event["only_name"]
        # print("final_path", final_path)
        new_files = []
        unique_destinations = set(self.destinations) - {0, None}
        for destination in unique_destinations:
            column_indices = [i for i, x in enumerate(self.destinations)
                              if x == destination or x == 0]

            subset_df = df.iloc[:, column_indices]
            csv_buffer = io.StringIO()
            subset_df.to_csv(csv_buffer, index=False,
                             header=False, sep="|", escapechar="\\")
            final_name = self.final_path.replace("NEW_ELEM_NAME", "destination")
            final_name = f"{final_name}_DEST_{destination}.csv"
            self.s3_utils.save_file_in_aws(csv_buffer.getvalue(), final_name)
            new_files.append(final_name)

        return {
            "new_files": new_files,
            "original_file": csv_file,
            "unique_destinations": list(unique_destinations)
        }
