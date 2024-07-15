from respond.models import DataFile
from data_param.models import FileControl
from inai.models import Petition
from task.base_views import TaskBuilder
from django.db.models import QuerySet
from task.helpers import HttpResponseError


class EarlyFinishError(Exception):

    def __init__(self, errors):
        self.errors = errors
        super().__init__(self.errors)


class MatchControls:

    def __init__(self, explore_class):

        self.data_file: DataFile = explore_class.data_file
        self.base_task: TaskBuilder = explore_class.base_task
        self.task_params = explore_class.task_params

        self.saved = False
        self.matched_controls = []
        self.errors = []
        self.name_columns_simple = None
        self.all_data_files = {}

        self.file_control = None
        self.already_cluster = True
        self.only_cols_with_headers = False
        # self.set_file_control(file_control or pfc.file_control)
        # self.file_control = file_control or pfc.file_control
        pfc = self.data_file.petition_file_control
        self.petition = pfc.petition
        self.set_file_control(pfc.file_control)

    def set_file_control(self, file_control):
        if not file_control:
            return
        self.file_control = file_control
        self.only_cols_with_headers = self.file_control.file_transformations \
            .filter(clean_function__name="only_cols_with_headers").exists()

    def find_in_file_controls(self, file_controls: QuerySet[FileControl]):
        self.already_cluster = False
        for file_control in file_controls:
            self.set_file_control(file_control)
            self.find_file_controls()

    def find_file_controls(self):
        from respond.views import SampleFile
        from respond.models import DataFile
        from respond.data_file_mixins.get_data_mix_real import ExtractorRealMix

        extractor = ExtractorRealMix(
            self.data_file, base_task=self.base_task, want_response=False)
        data = extractor.get_data_from_file(
            file_control=self.file_control, task_params=self.task_params)

        if not data:
            return False
        # print("data", data)
        current_sheets = data["current_sheets"]
        structured_data = data["structured_data"]
        if self.already_cluster:
            # print("INTENTO GUARDAR current_sheets", current_sheets)
            self.data_file.filtered_sheets = current_sheets
            self.data_file.save()
        # RICK BUGS
        is_match_ready = self._has_exact_matches(current_sheets)
        self.saved = is_match_ready
        if is_match_ready:
            return True, []
        print("data_file_id 4:", self.data_file.id)
        # is_orphan = file_ctrl.data_group.name == "orphan"

        same_data_files = DataFile.objects \
            .filter(file=self.data_file.file) \
            .exclude(petition_file_control__file_control__data_group_id="orphan")
        for df in same_data_files:
            self.all_data_files[df.petition_file_control_id] = df
        # name_columns_simple = NameColumn.objects.filter(
        #     file_control=file_ctrl, position_in_data__isnull=False)
        self.name_columns_simple = self.file_control.columns.filter(
            position_in_data__isnull=False)
        sorted_sheet_names = current_sheets.copy()
        other_sheets = [sheet for sheet in structured_data.keys()
                        if sheet not in sorted_sheet_names]
        sorted_sheet_names.extend(other_sheets)
        current_pfc = self.data_file.petition_file_control_id
        sheets_matched_ids = []
        sample_file = SampleFile()

        for sheet_name in sorted_sheet_names:
            # headers = validated_rows[row_headers-1] if row_headers else []
            self._find_coincidences_in_sheet(sheet_name, structured_data)

        if current_pfc in self.all_data_files:
            self.data_file.sheet_files.exclude(id__in=sheets_matched_ids) \
                .update(matched=False)
            is_match_ready = self._has_exact_matches(current_sheets)
            self.saved = is_match_ready
            # print("is_match_ready", is_match_ready)
            if not is_match_ready:
                error = "No todas las hojas filtradas coinciden con " \
                        "el grupo de control"
                return self.add_errors([error])
            # RICK EXPLORE: Esto no lo estoy considerando ahora
            # return all_data_files[current_pfc], saved, []
            return self.saved
        return self.saved
        # return all_data_files, saved, []

    def add_errors(self, errors):
        self.errors.extend(errors)
        return self.saved

    def _find_coincidences_in_sheet(self, sheet_name, structured_data):
        from respond.models import PetitionFileControl
        from scripts.common import similar, text_normalizer
        if not structured_data[sheet_name].get("headers"):
            if not self.file_control.row_headers:
                try:
                    total_cols = len(structured_data[sheet_name]["all_data"][0])
                    if total_cols == len(self.name_columns_simple):
                        same_headers = True
                    else:
                        return
                except Exception as e:
                    print("error intentando obtener headers", e)
                    return
            return
        else:
            name_columns = self.name_columns_simple \
                .values_list("std_name_in_data", flat=True)
            name_columns = list(name_columns)
            headers = structured_data[sheet_name]["headers"]
            headers = [text_normalizer(head, True) for head in headers]
            final_headers = headers
            if self.only_cols_with_headers:
                final_headers = [head for head in headers if head]
                name_columns = [head for head in name_columns if head]
            # print("name_columns_list", name_columns_list)
            # print("headers", headers, "\n")
            same_headers = name_columns == final_headers
            # print("same_headers", same_headers)
            if not same_headers:
                total_cols = len(structured_data[sheet_name]["all_data"][0])
                if total_cols != len(self.name_columns_simple):
                    return
                coincidences = 0
                need_save = []

                for (idx, name_col) in enumerate(self.name_columns_simple):
                    st_name = name_col.std_name_in_data
                    header = headers[idx]
                    if st_name == header:
                        coincidences += 1
                        continue
                    if name_col.alternative_names:
                        if header in name_col.alternative_names:
                            coincidences += 1
                            continue
                    if not self.already_cluster:
                        continue
                    if not st_name or not header:
                        coincidences += 1
                        continue
                    if similar(st_name, header) > 0.8:
                        alt_names = name_col.alternative_names or []
                        name_col.alternative_names = alt_names + [header]
                        need_save.append(name_col)
                        coincidences += 1
                if coincidences + 1 >= len(self.name_columns_simple):
                    same_headers = True
                    for name_col in need_save:
                        name_col.save()

        if not same_headers:
            return
        print("data_file_id 5:", self.data_file.id)

        # def save_sheet_file(d_file=data_file, save_sample_data=False):

        print("data_file_id 6:", data_file.id)
        if sheet_name not in current_sheets:
            if self.data_file.petition_file_control_id in self.all_data_files:
                self._save_sheet_file(data_file)
                data_file.add_warning(
                    "Hay hojas con el mismo formato, no incluidas en "
                    "por los filtros de inclusión y exclusión")
            return
        try:
            succ_pet_file_ctrl, created_pfc = PetitionFileControl.objects \
                .get_or_create(
                file_control=self.file_control, petition=self.petition)
        except PetitionFileControl.MultipleObjectsReturned:
            errors = ["El grupo de control está duplicado en la solicitud"]
            raise EarlyFinishError(errors)
            # return data_file, saved, errors
        # validated_data[sheet_name] = structured_data[sheet_name]
        current_pfc = succ_pet_file_ctrl.id
        already_in_pfc = current_pfc in self.all_data_files
        # if pet_file_saved:
        #     continue
        if self.all_data_files and not already_in_pfc:
            original_sheet_files = data_file.sheet_files.all()
            info_text = "El archivo está en varios grupos de control"
            data_file.add_warning(info_text)
            new_data_file = data_file
            new_data_file.pk = None
            new_data_file.petition_file_control = succ_pet_file_ctrl
            new_data_file.filtered_sheets = current_sheets
            # new_data_file.change_status("explore|finished")
            new_data_file.finished_stage('explore|finished')
            # new_data_file.sample_data = validated_data
            new_data_file.save()
            new_data_file.add_warning(info_text)
            self.all_data_files[current_pfc] = new_data_file
            for sheet_file in original_sheet_files:
                sheet_file.pk = None
                sheet_file.data_file = new_data_file
                if sheet_file.sheet_name == sheet_name:
                    sheet_file.matched = True
                    sheet_file.sample_data = structured_data[sheet_name]
                    sample_file.save_sample(
                        sheet_file, structured_data[sheet_name])
                elif sheet_file.matched == None:
                    sheet_file.matched = False
                sheet_file.save()
        else:
            current_file = self.all_data_files.get(current_pfc, data_file)
            # current_file.sample_data = validated_data
            save_sheet_file(current_file, True)
            if not self.saved and not self.already_cluster:
                current_file.filtered_sheets = current_sheets
            # RICK EXPLORE: No estoy seguro si saved puede ser global
            self.saved = True
            if not already_in_pfc:
                current_file.petition_file_control = succ_pet_file_ctrl
                # current_file = current_file.change_status("explore|finished")
                current_file.stage_id = "explore"
                current_file.status_id = "finished"
            current_file.save()
            self.all_data_files[current_pfc] = current_file

    def _save_sheet_file(self, d_file=data_file, save_sample_data=False):
        from respond.models import SheetFile

        try:
            sheet_f = d_file.sheet_files \
                .filter(sheet_name=sheet_name).first()
            if not sheet_f:
                original_sheet_f = data_file.sheet_files \
                    .filter(sheet_name=sheet_name).first()
                sheet_f = SheetFile.objects.create(
                    data_file=d_file,
                    sheet_name=sheet_name,
                    total_rows=original_sheet_f.total_rows,
                    sample_data=original_sheet_f.sample_data,
                    sample_file=original_sheet_f.sample_file,
                )
            if save_sample_data:
                # sheet_f.sample_data = structured_data[sheet_name]
                sample_file.save_sample(sheet_f, structured_data[sheet_name])
            sheet_f.matched = True
            sheet_f.save()
            sheets_matched_ids.append(sheet_f.id)
        except Exception as e:
            raise Exception(f"Para el archivo {data_file.id} no se "
                            f"encontró la hoja {sheet_name}; "
                            f"current_sheets: {current_sheets}\n-->{e}")

    def _has_exact_matches(self, filtered_sheets=None):
        # print("filtered_sheets", filtered_sheets)
        if not filtered_sheets or not self.data_file.sheet_files.exists():
            return False
        sheets_matched = self.data_file.sheet_files.filter(matched=True)\
            .values_list("sheet_name", flat=True).distinct()
        # print("sheets_matched", sheets_matched)
        if not sheets_matched.exists():
            return False
        set_sheets_matched = set(sheets_matched)
        set_filtered_sheets = set(filtered_sheets)
        # print("set_filtered_sheets", set_filtered_sheets)
        # print("set_sheets_matched", set_sheets_matched)
        return set_filtered_sheets.issubset(set_sheets_matched)

