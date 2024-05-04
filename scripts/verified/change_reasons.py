

def restructurate_reasons():
    from inai.models import PetitionNegativeReason
    from category.models import NegativeReason
    all_reasons = [
        ["Incompetencia", "Se declaran incompetentes para proporcionar esos datos, ya que no son los responsables.", "", ""],
        ["En proceso de validación", "La información solicitada aun se encuentra en proceso de validación por lo que no la tienen disponible.", "En proceso de validación", "Información no entregada por causas internas."],
        ["Sistema AAMATES", "Se encuentra en el sistema AAMATES y es administrado por el INSABI", "Información clasificada", ""],
        ["No expiden recetas", "Dicen no tener esos datos ya que el hospital no expide recetas y no cuenta con farmacia.", "No expiden recetas", "No proporcionan medicamentos "],
        ["No dan medicamentos", "No se dan medicamentos a los pacientes, ya que los compran por su cuenta.", "No dan medicamentos", ""],
        ["No cuentan con la información", "Dicen no tener la información pero no especifican porqué no.", "", ""],
        ["Dicen entregar la información pero no lo hacen", "Dicen que adjuntan la información en la plataforma o en el correo pero no lo hacen.", "En proceso de validación", ""],
        ["Información en físico en unidades médicas", "Tienen la información de forma física en las unidades medicas correspondientes. No procesan en una base de datos digital esa información.", "Información en físico en unidades médicas", "Información registrada solamente en físico"],
        ["Los datos solicitados no forman parte del registro en el sistema", "No registran algunas de las variables que solicitamos en sus mecanismos de registro internos.", "", ""],
        ["Recoger en oficinas", "El sujeto obligado no envía la información porque sobrepasa el tamaño para enviar por plataforma o mail. Piden se recoja en las oficinas.", "", ""],
        ["Datos equivocados otra solicitud", "Envían la información de alguna otra solicitud que no corresponde.", "En proceso de validación", ""],
        ["No la tienen porque es antigua", "El sujeto obligado no envía la información porque dice no tenerla. Ya que es información antigua y en ese tiempo no se procesaba la información de la manera que se solicita.", "", ""],
        ["Información clasificada", "El sujeto obligado refiere que los datos solicitados se consideran información clasificada, sin aportar argumentos o evidencia que apoye su argumento.", "Información clasificada", "No están en posesión o en condiciones de entregar la información"],
        ["Procesamiento por compañía subrogada", "No envían la información porque dicen que esos datos son procesados por compañías contratadas de manera externa y estas no comparten la información.", "Información clasificada", ""],
        ["Contiene datos personales", "El sujeto obligado no envía la información porque esta contiene datos personales de los pacientes y no les es posible des agregar la información.", "Información en físico en unidades médicas", ""],
        ["Sobrepasa las capacidades técnicas", "El sujeto obligado esta incapacitado para enviar la información porque recopilarla sobrepasa sus capacidades técnicas.", "Información en físico en unidades médicas", ""],
        ["No pueden producir documentos add doc", "El sujeto obligado se escusa en el articulo 129 y 130 de la Ley de Transparencia. Que dice que no están obligados a realizar documentos add doc para otorgar la información solicitada.", "", ""],
        ["Sin mecanismos de procesamiento de datos", "El sujeto obligado dice no tener la información por no tener un mecanismo que procese la información de la forma que se solicita.", "Información en físico en unidades médicas", ""],
    ]
    algo_mas = ["Información en físico en unidades médicas",
        "Contiene datos personales",
        "Sobrepasa las capacidades técnicas",
        "Sin mecanismos de procesamiento de datos"]
    for reason in algo_mas:
        current_new.description = "".join(current_new.description )
    for reason in all_reasons:
        name = reason[0]
        group_in = reason[2]
        new_name = reason[3]
        # print(name)
        current = NegativeReason.objects.get(name=name)
        if group_in == name:
            current.name = new_name
            current.save()
        if group_in and group_in != name:
            current_new = NegativeReason.objects.get(name=group_in)
            pet_negs = PetitionNegativeReason.objects.filter(
                negative_reason__name=name)
            # print(pet_negs.count())
            for pet_neg in pet_negs:
                already_neg = PetitionNegativeReason.objects.filter(
                    petition=pet_neg.petition, negative_reason__name=group_in)
                if not already_neg.exists():
                    pet_neg.negative_reason = current_new
                    #pet_neg.update(negative_reason=current_new)
                    pet_neg.save()
                elif pet_neg.is_main:
                    already_neg_obj = already_neg.first()
                    already_neg_obj.is_main = True
                    already_neg_obj.save()
                if already_neg.exists():
                    pet_neg.delete()
    #for PetitionNegativeReason in NegativeReason:


def set_file_type_to_datafile():
    from respond.models import DataFile
    from category.models import FileType
    all_files = DataFile.objects.all()
    for data_file in all_files:
        if data_file.file_type:
            continue
        data_file.file_type_id = 'original_data'
        data_file.save()


def change_some_default_values():
    from respond.models import DataFile
    all_files = DataFile.objects.all()
    fields = ['inserted_rows', 'completed_rows', 'total_rows']
    for data_file in all_files:
        for field in fields:
            if getattr(data_file, field) == 1:
                setattr(data_file, field, 0)
        data_file.save()


def name_columns_to_upper():
    from data_param.models import NameColumn
    all_names = NameColumn.objects.all()
    for name in all_names:
        if name.name_in_data:
            name.name_in_data = name.name_in_data.strip().upper()
            name.save()


# Deprecated
def recalculate_sheets():
    from scripts.common import explore_sheets

    from respond.models import DataFile
    from data_param.models import FileControl

    all_controls = FileControl.objects.all()
    # Esto no va a funcionar porque ya no existe status_process
    complete_controls = all_controls.filter(
        status_process__name="complete_counting")
    for file_control in complete_controls:
        include_names, exclude_names, include_idx, exclude_idx = explore_sheets(
            file_control)
        complete_files = DataFile.objects.filter(
            file_control__in=complete_controls, sample_data__isnull=False)
        for file in complete_files:
            if not file.sample_data or not file.sheet_names:
                continue
            filtered_sheets = []
            pending_sheets = []
            sheets_info = {"all": file.sheet_names}
            for position, sheet_name in enumerate(file.sheet_names, start=1):
                if include_names and sheet_name not in include_names:
                    continue
                if exclude_names and sheet_name in exclude_names:
                    continue
                if include_idx and position not in include_idx:
                    continue
                if exclude_idx and position in exclude_idx:
                    continue
                filtered_sheets.append(sheet_name)
            sheets_info["filtered"] = filtered_sheets


def results_to_warnings():
    from respond.models import DataFile
    files_with_results = DataFile.objects.filter(
        all_results__isnull=False).exclude(all_results__exact={})
    for file in files_with_results:
        # file.warnings = file.all_results
        # file.all_results = None
        # file.save()
        print(file.all_results)


def set_data_files_to_initial():
    from respond.models import DataFile
    all_data_files = DataFile.objects.all()
    all_data_files.update(stage_id="initial", status_id="finished")


def delete_child_data_files():
    from respond.models import DataFile
    all_data_files = DataFile.objects.filter(origin_file__isnull=False)
    all_data_files.delete()


def assign_column_to_special_transforms():
    from data_param.models import NameColumn, FinalField
    special_transforms = ["fragmented", "concatenated"]
    columns = NameColumn.objects.filter(
        column_transformations__clean_function__name__in=special_transforms)
    final_field = FinalField.objects.get(name="*concat_or_fragment")
    columns.update(final_field=final_field)

