import django


class DataUtilsMix:
    save: classmethod
    error_process: object
    status_process: object

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

    def finished_stage(self, status_name):
        # print("change_status", status_name)
        from category.models import StatusControl
        # self.error_process = list(set(self.error_process or []))
        self.error_process = []
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

    def comprobate_sheets(self, stage):
        stage_sheets = self.sheet_files.filter(stage_id=stage)

        def save_new_status(new_st):
            if not self.status_id == new_st:
                self.status_id = new_st
                self.error_process = []
                self.warnings = None
                if 'error' in new_st:
                    all_errors = stage_sheets\
                        .filter(status__macro_status='with_errors')\
                        .values_list('error_process', flat=True)
                    all_errors = list(set(all_errors))
                    if new_st == 'some_errors':
                        all_errors += self.warnings
                        all_errors.insert(0, f'Algunas hojas no se pudieron procesar en {stage}')
                        self.warnings = all_errors
                    elif new_st == 'with_errors':
                        self.error_process = list(set(all_errors))
                self.save()
            return self

        if stage_sheets.filter(status__is_completed=False).exists():
            return save_new_status('pending')
        every_status = stage_sheets.values_list('status_id', flat=True).distinct()
        every_status = list(set(every_status))
        new_status = every_status[0] if len(every_status) == 1\
            else 'some_errors'
        return save_new_status(new_status)
