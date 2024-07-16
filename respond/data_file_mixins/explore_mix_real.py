from task.base_views import TaskBuilder
from task.helpers import HttpResponseError
from respond.data_file_mixins.df_from_aws import FromAws as DataFileAws
from respond.data_file_mixins.get_data_mix_real import ExtractorRealMix
from respond.data_file_mixins.find_coincidences import MatchControls


def get_readeable_suffixes():
    from category.models import FileFormat
    readable_suffixes = FileFormat.objects.filter(readable=True) \
        .values_list("suffixes", flat=True)
    final_readeable = []
    for suffix in list(readable_suffixes):
        final_readeable += suffix
    return final_readeable


class ExploreRealMix(DataFileAws, ExtractorRealMix):
    readable_suffixes = get_readeable_suffixes()

    def __init__(self, want_response=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.want_response = want_response

    # Guardado en funciones y directo
    def get_sample_data(self, comprobate=False, **kwargs):

        sheet_names = self.data_file.sheet_names_list

        if sheet_names:
            return self.data_file

        # task_params["models"] = [data_file]
        self.data_file.warning = []
        self.data_file.error_process = []
        self.data_file.save()

        if not self.data_file.suffix:
            self._decompress_and_save_suffix()
        else:
            self.check_suffix_legible([self.data_file.suffix])
        self._get_sheet_files(**kwargs)
        if comprobate:
            self.base_task.comprobate_status(
                want_http_response=True, explore_parent=False)

    # Guardado en funciones
    def verify_coincidences(self, task_params, **kwargs):
        match_controls = MatchControls(self.data_file, self.base_task)
        match_controls.match_file_control()

    # Guardado en funciones
    def prepare_transform(self, task_params, **kwargs):
        from respond.data_file_mixins.matches_mix import MatchTransform
        self._count_file_rows()
        file_control = self.data_file.petition_file_control.file_control
        if file_control.is_intermediary:
            error = (
                "No se puede preparar muestra con la función " 
                "'Se repiten las mismas columnas', enviar 'Transformar'")
            return [], [error], self.data_file
        match_transform = MatchTransform(self.data_file, task_params)
        return match_transform.build_csv_converted(is_prepare=True)

    # Guardado en funciones
    def transform_data(self, task_params, **kwargs):
        from respond.data_file_mixins.matches_mix import MatchTransform
        from respond.data_file_mixins.intermediary_mix import Intermediary
        file_control = self.data_file.petition_file_control.file_control
        if file_control.is_intermediary:
            my_intermediary = Intermediary(self.data_file, task_params)
            return my_intermediary.split_columns()
        else:
            match_transform = MatchTransform(self.data_file, task_params)
            return match_transform.build_csv_converted(is_prepare=False)

    def _get_sheet_files(self, **kwargs):
        from respond.views import SampleFile
        from respond.models import SheetFile

        sample_file = SampleFile()
        sample_data = sample_file.get_sample(self.data_file)
        if self.data_file.suffix in self.xls_suffixes:
            return self.build_data_from_file(**kwargs)
        elif not sample_data:
            return self.build_data_from_file(**kwargs)
        # Esto pasa cuando ya hay guardados datos, pero no sus sheet_files
        else:
            default_sample = sample_data.get("default", {})
            previous_explore = default_sample and self.data_file.explore_ready
            if previous_explore and default_sample.get("tail_data"):
                total_rows = default_sample.pop("total_rows", 0)
                sample_file.create_file(
                    self.data_file,
                    cat_name="default_samples",
                    sample_data=default_sample)
                SheetFile.objects.create(
                    file=self.data_file.file,
                    data_file=self.data_file,
                    sheet_name="default",
                    file_type="clone",
                    matched=True,
                    sample_data=default_sample,
                    sample_file=sample_file.final_path,
                    total_rows=total_rows
                )
                self.data_file.filtered_sheets = ["default"]
                self.data_file.save()
            else:
                return self.build_data_from_file(**kwargs)

    def _count_file_rows(self):
        from respond.models import SheetFile
        from django.db.models import Sum
        file_control = self.data_file.petition_file_control.file_control
        minus_headers = file_control.row_start_data - 1
        total_count_query = SheetFile.objects.filter(
            data_file=self.data_file,
            sheet_name__in=self.data_file.filtered_sheets
        ).aggregate(Sum("total_rows"))
        total_count = total_count_query.get("total_rows__sum", 0)
        minus_headers = len(self.data_file.filtered_sheets) * minus_headers
        total_count -= minus_headers
        self.data_file.total_rows = total_count
        self.data_file.save()

    def _decompress_and_save_suffix(self):
        import pathlib
        import re
        # Se obtienen todos los tipos del archivo inicial:
        # print("final_path: ", self.final_path)
        final_path = self.data_file.final_path
        suffixes = pathlib.Path(final_path).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        re_is_suffix = re.compile(r'^\.([a-z]{3,4}|gz)$')
        suffixes = [suffix for suffix in suffixes
                    if bool(re.search(re_is_suffix, suffix))]
        split_sheet_files = self.data_file.sheet_files.filter(file_type='split')
        if '.gz' in suffixes:
            if not self.data_file.sheet_files.exists():
                self._decompress_gz_file()
            suffixes.remove('.gz')
        elif '.zip' in suffixes or '.rar' in suffixes:
            error = "Mover a 'archivos no finales' para descomprimir desde allí"
            self.base_task.add_errors_and_raise([error])
        elif len(suffixes) == 1 and not split_sheet_files.exists():
            # RICK TASK: A veces ocurre que esto está vacío...
            file_size = self.data_file.file.size
            if file_size > 440000000:
                real_suffix = suffixes[0]
                # RICK EXPLORE: Qué pasa con los .csv?
                if real_suffix not in self.xls_suffixes:
                    self._decompress_gz_file()

        real_suffixes = suffixes
        if len(real_suffixes) != 1:
            errors = [("Tiene más o menos extensiones de las que"
                       " podemos reconocer: %s" % real_suffixes)]
            return self.base_task.add_errors_and_raise(errors)
        # real_suffixes = set(real_suffixes)
        first_suffix = real_suffixes[0]
        if first_suffix:
            self.data_file.suffix = first_suffix
            self.data_file.save()
        self.check_suffix_legible(real_suffixes)

    def check_suffix_legible(self, suffixes: list):
        real_suffixes = set(suffixes)
        if not real_suffixes.issubset(self.readable_suffixes):
            error = "Formato no legible %s" % suffixes
            self.base_task.add_errors_and_raise([error])

    def _decompress_gz_file(self):
        from inai.models import set_upload_path

        directory = set_upload_path(self.data_file, "split/NEW_FILE_NAME")
        params = {
            "file": self.data_file.file.name,
            "directory": directory,
        }
        gz_task = TaskBuilder(
            function_name="decompress_gz", parent_class=self.base_task,
            models=[self.data_file], params=params)
        gz_task.async_in_lambda(http_response=True)
