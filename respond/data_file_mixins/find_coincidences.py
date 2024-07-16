from respond.models import DataFile
from data_param.models import FileControl
from inai.models import Petition
from task.base_views import TaskBuilder
from django.db.models import QuerySet
from task.helpers import HttpResponseError
from respond.data_file_mixins.get_data_mix_real import EarlyFinishError


class MatchControls:

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):

        self.data_file = data_file
        self.base_task = base_task
        self.already_cluster = True

        self.saved = False
        self.errors = []
        self.warnings = []
        self.full_sheet_data = {}

        self.sheet_matches = {}
        self.filtered_sheets: list[str] = []
        self.some_saved = False
        self.controls_matched = set()

        self.all_data_files = {}
        self.sheets_matched_ids = []

        self.file_control = None
        self.name_columns_simple = None

        self.only_cols_with_headers = False

        # self.set_file_control(file_control or pfc.file_control)
        # self.file_control = file_control or pfc.file_control
        self.original_pfc = self.data_file.petition_file_control
        self.is_orphan = self.original_pfc.file_control.data_group_id == "orphan"
        self.petition = self.original_pfc.petition
        self.set_file_control(self.original_pfc.file_control)

    def set_file_control(self, file_control):
        if not file_control:
            return
        self.file_control = file_control

    def find_in_file_controls(self, file_controls: QuerySet[FileControl]):
        self.already_cluster = False
        for file_control in file_controls:
            is_current_control = file_control == self.original_pfc.file_control
            self.set_file_control(file_control)
            try:
                matched = self.match_file_control()
            except EarlyFinishError as e:
                continue
        if self.controls_matched:
            pass
            # Acá necesitamos guardar las referencias

    def match_file_control(self):
        from respond.models import DataFile
        from respond.data_file_mixins.get_data_mix_real import ExtractorRealMix

        extractor = ExtractorRealMix(
            self.data_file, base_task=self.base_task,
            want_response=self.already_cluster)

        try:
            sheets_data = extractor.get_data_from_file(
                file_control=self.file_control)
            self.full_sheet_data, self.filtered_sheets = sheets_data
        except EarlyFinishError as e:
            return False

        # print("data", data)
        if self.already_cluster:
            self.data_file.filtered_sheets = self.filtered_sheets
            self.data_file.save()
            # RICK TASK: Había el comentario de RICK BUGS, no sé por qué...
            # Ahora lo estoy identando
            is_match_ready = self._has_exact_matches()
            if is_match_ready:
                return True

        # print("data_file_id 4:", self.data_file.id)

        self.name_columns_simple = self.file_control.columns.filter(
            position_in_data__isnull=False)
        # RICK FUTURE: esto lo voy a dejar sin usar por ahora
        # self.only_cols_with_headers = self.file_control.file_transformations \
        #     .filter(clean_function__name="only_cols_with_headers").exists()

        sorted_sheet_names = self.filtered_sheets.copy()
        other_sheets = [sheet for sheet in self.full_sheet_data.keys()
                        if sheet not in sorted_sheet_names]
        sorted_sheet_names.extend(other_sheets)

        for sheet_name in sorted_sheet_names:
            self._find_coincidences_in_sheet(sheet_name)

        if self.already_cluster:
            has_match = self._all_filtered_are_matched()

        else:
            for (sheet_name, match_data) in self.sheet_matches.items():
                self._save_matched_sheets(sheet_name, match_data)

        # RICK TASK: Aún no entiendo bien esta lógica y si debería
        # estar o no identada
        if not self.already_cluster:
            same_data_files = DataFile.objects \
                .filter(file=self.data_file.file) \
                .exclude(petition_file_control__file_control__data_group_id="orphan")
            self.sheets_matched_ids = []
            for df in same_data_files:
                self.all_data_files[df.petition_file_control_id] = df

            current_pfc = self.data_file.petition_file_control_id
            if current_pfc in self.all_data_files:
                self.data_file.sheet_files.exclude(id__in=self.sheets_matched_ids) \
                    .update(matched=False)
                is_match_ready = self._has_exact_matches()
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

    def _all_filtered_are_matched(self):
        if not self.filtered_sheets:
            raise EarlyFinishError("No hay hojas filtradas")
        if not self.full_sheet_data:
            raise EarlyFinishError("Ninguna hoja coincide con el grupo de control")
        matched_sheet_names = set(self.full_sheet_data.keys())
        if set(self.filtered_sheets) == matched_sheet_names:
            return True
        elif not set(self.filtered_sheets).issubset(matched_sheet_names):
            error = "No todas las hojas filtradas coinciden con el grupo de control"
            self.errors.append(error)
        else:
            warning = "Hay hojas con el mismo formato, no incluidas en " \
                    "por los filtros de inclusión y exclusión"
            self.data_file.add_warning(warning)
        return True

    def add_errors(self, errors):
        self.errors.extend(errors)
        return self.saved

    def _set_match(self, sheet_name, full=True):
        self.sheet_matches.setdefault(sheet_name, {"full": [], "simple": []})
        group = "full" if full else "simple"
        self.sheet_matches[sheet_name][group].append(self.file_control)
        self.controls_matched.add(self.file_control.id)
        return True

    def _find_coincidences_in_sheet(self, sheet_name):
        from scripts.common import text_normalizer
        sheet_data = self.full_sheet_data.get(sheet_name)

        try:
            first_row = sheet_data.get("all_data", [])[0]
            first_col = first_row[0]
            total_cols = len(first_row)
        except IndexError:
            raise EarlyFinishError("No se encontró información en la hoja")

        if not self.name_columns_simple.count() != total_cols:
            return False
        # RICK FUTURE: esto lo voy a dejar sin usar por ahora
        # if self.only_cols_with_headers:
        #     final_headers = [head for head in headers if head]
        #     name_columns = [head for head in name_columns if head]

        current_headers = sheet_data.get("headers")
        if not current_headers:
            if not self.file_control.row_headers:
                return self._set_match(sheet_name)
            return False

        std_headers = [text_normalizer(head, True) for head in current_headers]
        name_columns = list(self.name_columns_simple
                            .values_list("std_name_in_data", flat=True))

        if name_columns == std_headers:
            return self._set_match(sheet_name)
        return self._similar_matches(std_headers, sheet_name)

    def _similar_matches(self, std_headers, sheet_name):
        from scripts.common import similar, text_normalizer

        coincidences = 0
        need_save = []

        remain_headers = []
        for (idx, name_col) in enumerate(self.name_columns_simple):
            std_name = name_col.std_name_in_data
            header = std_headers[idx]
            if std_name == header:
                coincidences += 1
                continue
            if name_col.alternative_names:
                alt_names = [text_normalizer(alt_name, True)
                             for alt_name in name_col.alternative_names]
                if header in alt_names:
                    coincidences += 1
                    continue
            # if not self.already_cluster:
            #     continue
            remain_headers.append((name_col, header))

        if remain_headers and len(remain_headers) <= 3:
            for (name_col, header) in remain_headers:
                std_name = name_col.std_name_in_data
                if not std_name or not header:
                    coincidences += 1
                    continue
                if similar(std_name, header) > 0.8:
                    alt_names = name_col.alternative_names or []
                    name_col.alternative_names = alt_names + [header]
                    need_save.append(name_col)
                    coincidences += 1

        if coincidences + 2 >= len(self.name_columns_simple):
            for name_col in need_save:
                name_col.save()
            return self._set_match(sheet_name, False)
        return False

    def _save_matched_sheets(self, sheet_name, match_data):
        from respond.views import SampleFile
        from respond.models import PetitionFileControl

        print("data_file_id 5:", self.data_file.id)

        # def save_sheet_file(d_file=data_file, save_sample_data=False):
        final_matches = match_data.get("full", [])
        if not final_matches:
            final_matches = match_data.get("simple", [])

        # print("data_file_id 6:", data_file.id)
        if sheet_name not in self.filtered_sheets:
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
        # validated_data[sheet_name] = sheet_data
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
            new_data_file.filtered_sheets = filtered_sheets
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
                    sheet_file.sample_data = sheet_data
                    sample_file = SampleFile()
                    sample_file.save_sample(
                        sheet_file, sheet_data)
                elif sheet_file.matched == None:
                    sheet_file.matched = False
                sheet_file.save()
        else:
            current_file = self.all_data_files.get(current_pfc, data_file)
            # current_file.sample_data = validated_data
            self._save_sheet_file(current_file, True)
            if not self.saved and not self.already_cluster:
                current_file.filtered_sheets = filtered_sheets
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
                # sheet_f.sample_data = sheet_data
                sample_file.save_sample(sheet_f, sheet_data)
            sheet_f.matched = True
            sheet_f.save()
            self.sheets_matched_ids.append(sheet_f.id)
        except Exception as e:
            raise Exception(f"Para el archivo {data_file.id} no se "
                            f"encontró la hoja {sheet_name}; "
                            f"filtered_sheets: {filtered_sheets}\n-->{e}")

    def _has_exact_matches(self):
        sheet_files = self.data_file.sheet_files
        if not self.filtered_sheets or not sheet_files.exists():
            return False
        sheets_matched = sheet_files.filter(matched=True)\
            .values_list("sheet_name", flat=True).distinct()
        if not sheets_matched.exists():
            return False
        return set(self.filtered_sheets).issubset(set(sheets_matched))

