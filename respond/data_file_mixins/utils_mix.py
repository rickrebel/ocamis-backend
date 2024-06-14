import django


class DataUtilsMix:
    save: classmethod
    error_process: object

    def save_errors(self, errors, error_name):

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
            self.stage_id = 'initial'
            self.status_id = 'with_errors'
        # print(curr_errors)
        self.save()
        return self

    def finished_stage(self, status_name):
        # print("change_status", status_name)
        # self.error_process = list(set(self.error_process or []))
        self.error_process = []
        if "|" in status_name:
            split_name = status_name.split("|")
            stage = split_name[0]
            status = split_name[1]
            self.status_id = status
            self.stage_id = stage
        else:
            self.stage_id = 'initial'
            self.status_id = 'with_errors'
            self.error_process = [f"No se encontró el status {status_name}"]
        self.save()
        return self

    def reset_initial(self):
        self.stage_id = 'initial'
        self.status_id = 'finished'
        self.sheet_files.all().delete()
        self.filtered_sheets = []
        self.total_rows = 0
        self.suffix = None
        self.warnings = None
        self.error_process = None
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
            if self.status_id != new_st:
                self.status_id = new_st
                self.error_process = []
                self.warnings = None
                if 'error' in new_st:
                    all_errors = stage_sheets\
                        .filter(status__macro_status='with_errors')\
                        .values_list('error_process', flat=True)
                    print("all_errors", all_errors)
                    every_errors = []
                    for error in all_errors:
                        every_errors += error
                    all_errors = list(set(every_errors))
                    if new_st == 'some_errors':
                        all_errors += (self.warnings or [])
                        all_errors.insert(0, f'Algunas hojas no se pudieron procesar en {stage}')
                        self.warnings = all_errors
                    elif new_st == 'with_errors':
                        print("all_errors", all_errors)
                        self.error_process = list(set(list(all_errors)))
                self.save()
            return self

        if stage_sheets.filter(status__is_completed=False).exists():
            return save_new_status('pending')
        every_status = stage_sheets.values_list('status_id', flat=True).distinct()
        every_status = list(set(every_status))
        new_status = every_status[0] if len(every_status) == 1\
            else 'some_errors'
        return save_new_status(new_status)
