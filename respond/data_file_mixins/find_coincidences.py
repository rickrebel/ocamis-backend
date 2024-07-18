from respond.models import DataFile, SheetFile
from django.db.models import QuerySet
from data_param.models import FileControl
from task.builder import TaskBuilder
from task.helpers import HttpResponseError
from respond.data_file_mixins.get_data_mix import ExtractorRealMix
from respond.data_file_mixins.get_data_mix import EarlyFinishError


class MatchControls(ExtractorRealMix):

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):

        self.warnings = []
        super().__init__(data_file, base_task, True)

        self.find_many = False
        self.match_count = 0
        self.matched_sheets = {}

        self.sheets_matched_ids = []

        self.file_control = None
        self.name_columns = None

        self.twins_data_files = DataFile.objects\
            .filter(file=self.data_file.file)\
            .exclude(id=self.data_file.id) \
            .exclude(petition_file_control__file_control__data_group_id="orphan")
        self.pending_twins: dict[int, DataFile] = {}
        self.pending_twins = {df.petition_file_control_id: df
                              for df in self.twins_data_files}
        # self.only_cols_with_headers = False

        # self.set_file_control(file_control or pfc.file_control)
        # self.file_control = file_control or pfc.file_control
        initial_pfc = self.data_file.petition_file_control
        self.init_fc_id = initial_pfc.file_control.id
        self.pfc_is_orphan = initial_pfc.file_control.data_group_id == "orphan"

        self.petition = initial_pfc.petition

    def set_file_control(self, file_control):
        if not file_control:
            return
        self.file_control = file_control

    def _send_raise(self, error):
        if self.find_many:
            raise EarlyFinishError(error)
        self.data_file.save_errors([error], "cluster|with_errors")
        self.base_task.add_errors_and_raise([error])

    def find_in_file_controls(self):
        file_controls = self._get_related_file_controls()

        self.find_many = True
        self.want_response = False
        for file_control in file_controls:
            try:
                self.match_file_control(file_control)
            except EarlyFinishError as e:
                continue
        # RICK TASK2: Aún no entiendo bien esta lógica y si debería
        # estar o no identada
        self._check_twins()
        if not self.match_count:
            error = "No se encontraron coincidencias en ningún grupo de control"
            self.data_file.save_errors([error], "cluster|with_errors")
            self.base_task.add_errors_and_raise([error])

    def match_file_control(self, file_control=None):

        self.matched_sheets = {}
        # try:
        # se obtiene full_sheet_data, filtered_sheets, has_split, "is_valid"
        self.get_data_from_file(file_control or self.file_control)
        # except EarlyFinishError as e:
        #     return False
        if self.is_orphan:
            self._send_raise("No se puede comparar con orphan (sin grupo)")

        if not self.find_many:
            # RICK TASK2: Había el comentario de RICK BUGS, no sé por qué...
            # Ahora lo estoy identando
            # RICK TASK2: TODO: Hay que hacer un método sencillo cuando \
            # ya estaba agrupado para que no tarde tanto
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

        # if not self.find_many:
        self._save_matched_sheets()
        self.match_count += 1

    def _get_related_file_controls(self) -> QuerySet[FileControl]:

        has_real_provider = getattr(self.petition, "real_provider", None)

        base_controls = FileControl.objects \
            .filter(file_format__isnull=False) \
            .exclude(data_group_id="orphan")

        if has_real_provider:
            provider = self.petition.real_provider
            provider_controls = base_controls \
                .filter(petition_file_control__petition__real_provider=provider) \
                .distinct()
        else:
            provider = self.petition.agency.provider
            provider_controls = base_controls \
                .filter(petition_file_control__petition__agency__provider=provider) \
                .distinct()
        if not self.pfc_is_orphan:
            same_group_controls = provider_controls.filter(id=self.init_fc_id)
            provider_controls = provider_controls.exclude(id=self.init_fc_id)
            return same_group_controls | provider_controls
        return provider_controls

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
            return

        if not filtered_sheets.intersection(matched_sheets):
            return self._add_error(
                "Hay coincidencias, pero no en las hojas filtradas")
        if self.has_split:
            return

        error = "No todas las hojas filtradas coinciden con el grupo de control"
        warning = "Hay hojas que coinciden, pero no se incluyeron en los filtros"
        if matched_sheets.issubset(filtered_sheets):
            self._add_error(error)
        elif filtered_sheets.issubset(matched_sheets):
            self._add_warning(warning)
        else:
            self._add_error(error)
            self._add_warning(warning)

    def _add_error(self, text):
        self.errors.append(text)

    def _add_warning(self, text):
        self.warnings.append(text)

    def _set_match(self, sheet_name, full=True):
        self.matched_sheets[sheet_name] = True

    def _find_coincidences_in_sheet(self, sheet_name):
        sheet_data = self.full_sheet_data.get(sheet_name)
        if sheet_data.get("is_valid") is False:
            return

        try:
            first_row = sheet_data.get("all_data", [])[0]
            first_col = first_row[0]
            total_cols = len(first_row)
        except IndexError:
            raise "No se encontró información en la hoja"

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

    # def _set_pfc(self, data_file: DataFile, file_control: FileControl = None):
    def _set_pfc(self, data_file: DataFile):
        from respond.models import PetitionFileControl
        pet_file_ctrl, _ = PetitionFileControl.objects.get_or_create(
            file_control=self.file_control, petition=self.petition)
        data_file.petition_file_control = pet_file_ctrl
        return data_file

    # def _save_matched_sheets(self, file_control_data: dict = None):
    def _save_matched_sheets(self):
        is_create = bool(self.match_count)

        if self.file_control.id in self.pending_twins:
            data_file = self.pending_twins.pop(self.file_control.id)
            if data_file.stage_ready("pre_transform"):
                return
            data_file.sheet_files.all().delete()
            is_create = True
        elif is_create:
            data_file = self._save_new_data_file()
            data_file.save()
        else:
            data_file = self.data_file

        if is_create or self.pfc_is_orphan:
            data_file = self._set_pfc(data_file)
        elif not self.init_fc_id != self.file_control.id:
            data_file = self._set_pfc(data_file)

        data_file.filtered_sheets = self.filtered_sheets
        data_file.errors = self.errors or None
        data_file.warnings = self.warnings or None
        for sheet_file in self.data_file.sheet_files.all():
            if is_create:
                sheet_file = self._save_new_sheet_file(data_file, sheet_file)

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
            # sheet_file.stage_id = "cluster"
            # sheet_file.status_id = "finished"
            sheet_file.save()
        status = "finished" if not self.errors else "with_errors"
        data_file.finished_stage(f"cluster|{status}")

    # def _save_new_data_file(self, control_data):
    def _save_new_data_file(self):
        # RICK TASK2: TODO: debemos considerar si es el mismo archivo
        general_warning = "El archivo está en varios grupos de control"
        self.warnings.append(general_warning)

        if self.match_count < 2:
            self.data_file.is_duplicate = False
            self.data_file.warnings = (self.warnings or []) + [general_warning]
            self.data_file.save()

        return DataFile(
            file=self.data_file.file,
            provider=self.data_file.provider,
            is_duplicate=False,
            date=self.data_file.date,
            suffix=self.data_file.suffix,
            directory=self.data_file.directory,
            total_rows=self.data_file.total_rows,
            sample_file=self.data_file.sample_file,
            sheet_names=self.full_sheet_data.keys(),
            notes=self.data_file.notes,
        )

    def _save_new_sheet_file(self, data_file: DataFile, sheet_file: SheetFile):

        return SheetFile(
            data_file=data_file,
            file=sheet_file.file,
            file_type=sheet_file.file_type,
            sheet_name=sheet_file.sheet_name,
            total_rows=sheet_file.total_rows,
            sample_file=sheet_file.sample_file,
        )

    def _check_twins(self):

        for file_control_id, data_file in self.pending_twins.items():
            if data_file.stage_ready("pre_transform"):
                continue
            data_file.sheet_files.all().update(matched=False)
            errors = ["Un análisis posterior detectó que no hay coincidencias"]
            if self.match_count:
                errors.append(
                    "Sin embargo, el archivo ya se encuentra otro grupo de control")
            data_file.save_errors(errors, "cluster|with_errors")
