import django


class DataUtilsMix:
    save: classmethod
    error_process: object
    status_process: object
    all_results: object

    def save_errors(self, errors, error_name):
        from rest_framework.response import Response
        from rest_framework import (permissions, views, status)
        from category.models import StatusControl

        #errors = ['No se pudo descomprimir el archivo gz']
        curr_errors = self.error_process or []
        curr_errors += errors
        # print("error_name", error_name)
        current_status, created = StatusControl.objects.get_or_create(
            name=error_name, group="process")
        curr_errors = list(set(curr_errors))
        self.error_process = curr_errors
        self.status_process = current_status
        # print(curr_errors)
        self.save()
        return self

    def change_status(self, status_name):
        from category.models import StatusControl
        new_status, created = StatusControl.objects.get_or_create(
                name=status_name, group="process")
        self.error_process = list(set(self.error_process or []))
        self.status_process = new_status
        self.save()
        return self

    def add_result(self, new_result):
        curr_result = self.all_results or {}
        if new_result[0] in curr_result.keys():
            curr_result[new_result[0]] += f", {new_result[1]}"
        self.all_results = curr_result
        self.save()

    def massive_insert_copy(self, errors, error_name):
        #guardo esto para considerarlo en "missing_rows":
        """
        MissingRow.objects.create(
            file=file,
            original_data=row_data,
            row_seq=row_seq,
            errors=["Conteo distinto de Columnas %s" % len(row_data)],
        )"""
        return 2

    def build_task_params(self, function_name, request):
        from inai.models import AsyncTask
        from datetime import datetime
        key_task = AsyncTask.objects.create(
            user=request.user, function_name=function_name,
            data_file=self, date_start=datetime.now(),
            status_task_id="created"
        )
        return {
            "parent_task": key_task
        }


