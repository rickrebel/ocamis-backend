from respond.models import DataFile
from django.db.models import QuerySet
from data_param.models import FileControl
from inai.models import Petition
from task.base_views import TaskBuilder
from task.helpers import HttpResponseError
from respond.data_file_mixins.get_data_mix_real import ExtractorRealMix
from respond.data_file_mixins.get_data_mix_real import EarlyFinishError


class MatchControls(ExtractorRealMix):

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):

        self.warnings = []
        super().__init__(data_file, base_task, True)
        # Inútiles:
        self.saved = False
        self.some_saved = False

        self.find_many = False

        self.matched_sheets = {}
        self.matched_controls = {}

        self.all_data_files = {}
        self.sheets_matched_ids = []

        self.file_control = None
        self.name_columns = None
        # self.only_cols_with_headers = False

        # self.set_file_control(file_control or pfc.file_control)
        # self.file_control = file_control or pfc.file_control
        initial_pfc = self.data_file.petition_file_control
        self.init_file_control = initial_pfc.file_control
        self.pfc_is_orphan = self.init_file_control.data_group_id == "orphan"

        self.petition = initial_pfc.petition

    def set_file_control(self, file_control):
        if not file_control:
            return
        self.file_control = file_control

    def find_in_file_controls(self, file_controls: QuerySet[FileControl]):
        self.find_many = True
        self.want_response = False
        for file_control in file_controls:
            # is_current_control = file_control == self.init_pfc.file_control
            try:
                self.match_file_control(file_control)
            except EarlyFinishError as e:
                continue
        # RICK TASK2: Aún no entiendo bien esta lógica y si debería
        # estar o no identada
        self._check_twins()
        if not self.matched_controls:
            self.base_task.add_errors_and_raise(
                ["No se encontraron coincidencias"])
            # Acá necesitamos guardar las referencias
        elif len(self.matched_controls) == 1:
            self.saved = True

    def _send_raise(self, error):
        if self.find_many:
            raise EarlyFinishError(error)
        self.base_task.add_errors_and_raise([error])

    def match_file_control(self, file_control=None):

        self.matched_sheets = {}
        # try:
        # se obtiene full_sheet_data, filtered_sheets y has_split
        self.get_data_from_file(file_control or self.file_control)
        # except EarlyFinishError as e:
        #     return False
        if self.is_orphan:
            self._send_raise("No se puede comparar con orphan (sin grupo)")

        # print("data", data)
        if not self.find_many:
            # RICK TASK2: Había el comentario de RICK BUGS, no sé por qué...
            # Ahora lo estoy identando
            # RICK TASK2: No estoy seguro de la utilidad de esto
            is_match_ready = self._has_exact_matches()
            if is_match_ready:
                self.data_file.filtered_sheets = self.filtered_sheets
                self.data_file.save()
                return True

        self.name_columns = self.file_control.columns.filter(
            position_in_data__isnull=False)
        # RICK FUTURE: esto lo voy a dejar sin usar por ahora
        # self.only_cols_with_headers = self.file_control.file_transformations \
        #     .filter(clean_function__name="only_cols_with_headers").exists()

        if self.has_split:
            first_sheet_name = next(iter(self.filtered_sheets))
            self._find_coincidences_in_sheet(first_sheet_name)
        else:
            for sheet_name in self.full_sheet_data.keys():
                self._find_coincidences_in_sheet(sheet_name)

        if not self.matched_sheets:
            self._send_raise("Ninguna hoja coincide con el grupo de control")

        self._all_filtered_are_matched()

        if not self.find_many:
            self._save_matched_sheets()

    def _has_exact_matches(self):
        sheet_files = self.data_file.sheet_files
        if not self.filtered_sheets or not sheet_files.exists():
            return False
        sheets_matched = sheet_files.filter(matched=True)\
            .values_list("sheet_name", flat=True).distinct()
        if not sheets_matched.exists():
            return False
        return set(self.filtered_sheets).issubset(set(sheets_matched))

    def _all_filtered_are_matched(self):
        matched_sheets = set(self.matched_sheets.keys())
        filtered_sheets = set(self.filtered_sheets)

        if filtered_sheets == matched_sheets:
            return True

        if not filtered_sheets.intersection(matched_sheets):
            return self._add_error(
                "Hay coincidencias, pero no en las hojas filtradas")

        error = "No todas las hojas filtradas coinciden con el grupo de control"
        warning = "Hay hojas que coinciden, pero no se incluyeron en los filtros"
        if filtered_sheets.issubset(matched_sheets):
            self._add_warning(warning)
        elif matched_sheets.issubset(filtered_sheets):
            self._add_error(error)
        else:
            self._add_error(error)
            self._add_warning(warning)
        return True

    def _add_error(self, text, group="error"):
        if self.find_many:
            self.matched_controls[self.file_control.id]["errors"].add(text)
        else:
            self.errors.append(text)
        return True

    def _add_warning(self, text):
        self._add_error(text, "warning")

    def _set_match(self, sheet_name, full=True):
        self.matched_sheets.setdefault(sheet_name, {"full": [], "simple": []})
        group = "full" if full else "simple"
        self.matched_sheets[sheet_name][group].append(self.file_control)
        self.matched_controls[self.file_control.id].setdefault(
            {"sheet_names": set(), "warnings": set(), "errors": set()})
        self.matched_controls[self.file_control.id]["sheet_names"].add(sheet_name)
        return True

    def _find_coincidences_in_sheet(self, sheet_name):
        sheet_data = self.full_sheet_data.get(sheet_name)

        try:
            first_row = sheet_data.get("all_data", [])[0]
            first_col = first_row[0]
            total_cols = len(first_row)
        except IndexError:
            raise EarlyFinishError("No se encontró información en la hoja")

        if not self.name_columns.count() != total_cols:
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

        std_headers = sheet_data.get("std_headers")
        std_name_columns = list(
            self.name_columns.values_list("std_name_in_data", flat=True))
        if std_name_columns == std_headers:
            return self._set_match(sheet_name)
        return self._similar_matches(std_headers, sheet_name)

    def _similar_matches(self, std_headers, sheet_name):
        from scripts.common import similar, text_normalizer

        coincidences = 0
        need_save = []

        remain_headers = []
        for (idx, name_col) in enumerate(self.name_columns):
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

        if coincidences + 2 >= len(self.name_columns):
            for name_col in need_save:
                name_col.save()
            return self._set_match(sheet_name, False)
        return False

    def _check_twins(self):
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
            # RICK TASK2: No estoy seguro de la utilidad de esto
            is_match_ready = self._has_exact_matches()
            self.saved = is_match_ready
            # print("is_match_ready", is_match_ready)
            if not is_match_ready:
                error = "No todas las hojas filtradas coinciden con " \
                        "el grupo de control"
                self.errors.append(error)
                return self.saved
            # RICK TASK2: Esto no lo estoy considerando ahora
            # return all_data_files[current_pfc], saved, []
            return self.saved
        return self.saved
        # return all_data_files, saved, []

    def _get_pfc(self, file_control=None):
        from respond.models import PetitionFileControl
        if not file_control:
            file_control = self.file_control
        pet_file_ctrl, _ = PetitionFileControl.objects.get_or_create(
            file_control=file_control, petition=self.petition)
        return pet_file_ctrl

    def _save_matched_sheets(self):
        if self.pfc_is_orphan:
            new_pfc = self._get_pfc()
            self.data_file.petition_file_control = new_pfc
        self.data_file.filtered_sheets = self.filtered_sheets
        self.data_file.errors = self.errors or None
        self.data_file.warnings = self.warnings or None
        for sheet_file in self.data_file.sheet_files.all():
            sheet_data = self.full_sheet_data.get(sheet_file.sheet_name)
            is_second = sheet_data.get("is_second", False)
            if is_second:
                sheet_file.row_start_data = 1
                is_matched = True
            else:
                is_matched = sheet_file.sheet_name in self.matched_sheets
            sheet_file.matched = is_matched
            if is_matched:
                sheet_data.headers = sheet_data.get("headers")
            else:
                sheet_data.headers = []
            sheet_file.stage_id = "cluster"
            sheet_file.status_id = "finished"
            sheet_file.save()
        status = "finished" if not self.errors else "with_errors"
        self.data_file.finished_stage(f"cluster|{status}")

    def _save_many_matched_sheets(self, sheet_name, match_data):
        from respond.views import SampleFile

        print("data_file_id 5:", self.data_file.id)

        for (file_control, match_data) in self.matched_controls.items():
            # same_file_control = self.init_file_control.id == self.file_control.id
            if not match_data["sheet_names"]:
                continue
            if not match_data["errors"]:
                continue
            if not match_data["warnings"]:
                continue

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
            new_data_file.filtered_sheets = self.filtered_sheets
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
            if not self.saved and self.find_many:
                current_file.filtered_sheets = self.filtered_sheets
            # RICK TASK2: No estoy seguro si saved puede ser global
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
                            f"filtered_sheets: {self.filtered_sheets}\n-->{e}")
