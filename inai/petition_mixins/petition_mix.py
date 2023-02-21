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
        # print("comienza find_matches_in_children", "\n")
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
            ctrl_list = list(all_file_controls.values_list("id", flat=True))
            curr_kwargs = {
                "after_if_empty": "find_matches_in_file_controls",
                "after_params_if_empty": {
                    "all_file_controls_ids": ctrl_list
                },
                "current_file_ctrl": current_file_ctrl,
                "all_tasks": all_tasks,
                "all_errors": all_errors,
            }

            all_tasks, all_errors, data_file = data_file.get_sample_data(
                task_params, **curr_kwargs)
            # print("Nuevos tasks y errors:", "\n", all_tasks, "\n", all_errors, "\n")
            if not data_file:
                continue
            task_params["models"] = [data_file]
            new_body = {
                "all_file_controls": all_file_controls,
                "petition": self
            }
            data_file.find_matches_in_file_controls(
                task_params=task_params, **new_body)

        return all_tasks, all_errors
