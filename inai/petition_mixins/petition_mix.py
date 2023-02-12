class PetitionMix:
    petition_months: None

    def first_year_month(self):
        return self.petition_months.earliest().month_entity.year_month

    def last_year_month(self):
        return self.petition_months.latest().month_entity.year_month

    def months(self):
        html_list = ''
        start = self.petition_months.earliest().month_entity.human_name
        end = self.petition_months.latest().month_entity.human_name
        return " ".join(list(set([start, end])))
    months.short_description = u"Meses"

    def months_in_description(self):
        from django.utils.html import format_html
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        curr_months = []
        if self.description_petition:
            description = self.description_petition.lower()
            for month in months:
                if month in description:
                    curr_months.append(month)
            html_list = ''
            for month in list(curr_months):
                html_list = html_list + ('<span>%s</span><br>' % month)
            return format_html(html_list)
        else:
            return "Sin descripción"
    months_in_description.short_description = u"Meses escritos"


class PetitionTransformsMix(PetitionMix):
    entity: None

    def find_matches_in_children(
            self, all_data_files, current_file_ctrl=None, task_params=None):
        from inai.models import FileControl
        # self.__module__
        # cls = self.__class__
        entity_file_controls = FileControl.objects.filter(
            petition_file_control__petition__entity=self.entity,
            file_format__isnull=False) \
            .exclude(data_group__name="orphan") \
            .prefetch_related("columns") \
            .distinct()
        all_errors = []
        all_tasks = []

        if current_file_ctrl:
            entity_file_controls = entity_file_controls.filter(
                id=current_file_ctrl)

        near_file_controls = entity_file_controls\
            .filter(petition_file_control__petition=self)\
            .prefetch_related("file_format")
        others_file_controls = entity_file_controls\
            .exclude(petition_file_control__petition=self)\
            .prefetch_related("file_format")

        all_file_controls = near_file_controls | others_file_controls
        for data_file in all_data_files:
            data_file.error_process = []
            data_file.save()
            task_params = task_params or {}
            task_params["models"] = [data_file]
            (data_file, errors, suffix), first_task = data_file.decompress_file(
                task_params=task_params)
            if not data_file:
                print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
            elif not data_file.explore_data:
                task_params["function_after"] = "find_matches_in_file_controls"
                params_after = task_params.get("params_after", {})
                params_after["suffix"] = suffix
                params_after["all_file_controls_ids"] =\
                    list(all_file_controls.values_list("id", flat=True))
                task_params["params_after"] = params_after
                data_file, errors, new_task = data_file.transform_file_in_data(
                    'only_save', suffix, current_file_ctrl,
                    task_params=task_params)
                if new_task:
                    all_tasks.append(new_task)
                    continue
            if errors:
                all_errors.append(errors)
                continue
            body = {
                "suffix": suffix,
                "all_file_controls": all_file_controls,
                "petition": self
            }
            data_file.find_matches_in_file_controls(
                task_params=task_params, **body)
            if errors:
                all_errors.append(errors)
        return all_tasks, all_errors
