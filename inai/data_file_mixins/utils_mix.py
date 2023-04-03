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
        curr_errors = list(set(curr_errors))
        self.error_process = curr_errors
        # print("error_name", error_name)
        if "|" in error_name:
            split_name = error_name.split("|")
            stage = split_name[0]
            status = split_name[1]
            self.status_id = status
            self.stage_id = stage
        else:
            current_status, created = StatusControl.objects.get_or_create(
                name=error_name, group="process")
            self.status_process = current_status
        # print(curr_errors)
        self.save()
        return self

    def change_status(self, status_name):
        print("change_status", status_name)
        from category.models import StatusControl
        self.error_process = list(set(self.error_process or []))
        if "|" in status_name:
            split_name = status_name.split("|")
            stage = split_name[0]
            status = split_name[1]
            self.status_id = status
            self.stage_id = stage
        else:
            new_status, created = StatusControl.objects.get_or_create(
                    name=status_name, group="process")
            self.status_process = new_status
        self.save()
        return self

    def add_warning(self, warning_text):
        current_warnings = self.warnings or []
        if warning_text not in current_warnings:
            current_warnings.append(warning_text)
            self.warnings = current_warnings
            self.save()
