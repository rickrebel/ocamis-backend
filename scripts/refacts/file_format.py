
def refact_file_format():
    from respond.models import DataFile
    from data_param.models import FileControl
    from category.models import FileFormat
    original_formats = {
        "pdf": {
            "public_name": "PDF",
            "suffixes": ["pdf"],
            "readable": False,
            "order": 4
        },
        "word": {
            "public_name": "Word",
            "suffixes": ["doc", "docx"],
            "readable": False,
            "order": 1
        },
        "xls": {
            "public_name": "Excel",
            "suffixes": ["xls", "xlsx", "xlsb"],
            "readable": True,
            "order": 1
        },
        "txt": {
            "public_name": "Texto (.txt)",
            "suffixes": ["txt"],
            "readable": True,
            "order": 3
        },
        "csv": {
            "public_name": "CSV",
            "suffixes": ["csv"],
            "readable": True,
            "order": 2
        },
        "email": {
            "public_name":"Correo electrónico",
            "suffixes": [],
            "readable": False,
            "order": 5
        },
        "other": {
            "public_name": "Otro",
            "suffixes": [],
            "readable": False,
            "order": 6
        },
    }
    all_controls = FileControl.objects.all()
    for key, values in original_formats.items(): 
        curr_format_obj, created = FileFormat.objects.get_or_create(
            short_name=key,
            suffixes=values["suffixes"],
            public_name=values["public_name"],
            readable=values["readable"],
            order=values["order"],
        )
        all_controls.filter(format_file=key).update(file_format=curr_format_obj)


def refact_agency_in_file_control():
    from data_param.models import FileControl
    all_controls = FileControl.objects.all()
    for control in all_controls:
        pfc = control.petition_file_control.first()
        if pfc:
            control.agency = pfc.petition.agency
            #print(pfc.petition.agency)
            control.save()
        else:
            control.delete()

# refact_agency_in_file_control()
