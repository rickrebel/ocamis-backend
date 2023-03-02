
#from desabasto.recipe_report_scriptsv3 import massive_upload_csv_to_db
#massive_upload_csv_to_db("issste", [2021])


def generate_key2():
    import re
    from desabasto.models import Container
    all_conts = Container.objects.all()
    for cont in all_conts:
        cont.key2 = re.sub(r'(\.)', '', cont.key)
        cont.save()


def clean_old_imports():
    #from desabasto.models import (
    #    Container, CLUES, PrescriptionLog, Doctor, MedicalSpeciality)
    from formula.models import PrescriptionLog, Doctor, MedicalSpeciality
    from catalog.models import CLUES
    from medicine.models import Container
    Container.objects.filter(presentation__isnull=True).delete()
    CLUES.objects.filter(clues__isnull=True).delete()
    PrescriptionLog.objects.all().delete()
    MedicalSpeciality.objects.all().delete()
    if not Doctor.objects.filter(clave_doctor='1000000000').exists():
        med_spec, created = MedicalSpeciality.objects.create(name='unknown')
        Doctor.objects.create(
            nombre_medico="unknown", clave_doctor=1000000000,
            especialidad_medico=med_spec.id)


constant_path = "C:\\git\\rick_\\Desktop\\nosotrxs\\issste\\"


base_path = 'issste\\reporte_recetas_202111_'

def others():
    import io
    for num in range(5):
        print(num)
        reporte_recetas_path = "%s%s%s" % (base_path, num + 1, '.csv')
        with_coma = False
        try:
            #with open(reporte_recetas_path) as file:
            #with io.open(reporte_recetas_path, "r", encoding="utf-8") as file:
            with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
                data = file.read()
                rr_data_rows = data.split("\n")
                print(reporte_recetas_path)
                print(len(rr_data_rows))
                file.close()
        except Exception as e:
            print (e)

    import io
    reporte_recetas_path = 'imss\\req_julio_2019_02.txt'
    with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
        data = file.read()
        print(data[:30000])
