
# # Eliminando los penúltimos caracteres cuando son '00'
# def update_med_container_id():
#     from med_cat.models import Medicament
#     from medicine.models import Container
#     from geo.models import Provider
#     entity_imss = Provider.objects.get(id=55)
#     medicaments_own_imss = Medicament.objects.filter(
#         entity=entity_imss)
#     errors = {
#         "Key no encontrada": [], "No tiene formato correcto": [],
#         "Multiples contenedores": [], "Otros errores": []}
#     success_count = 0
#
#     for medicament in medicaments_own_imss:
#         # Llave sin los 00 insertados en la posición [10] y [11]
#         medi_own_key2 = medicament.own_key2[:-4] + medicament.own_key2[-2:]
#         # Complemento de medi_own_key2, es decir, los caracteres extra
#         # agregados, '00'
#         comp_medi_own_key2 = medicament.own_key2[-4:-2]
#         if comp_medi_own_key2 == '00':
#             try:
#                 container_found = Container.objects.get(key2=medi_own_key2)
#                 success_count += 1
#                 medicament.container = container_found
#                 # medicament.save()
#             except Container.DoesNotExist:
#                 errors["Key no encontrada"].append(medi_own_key2)
#                 continue
#             except Container.MultipleObjectsReturned:
#                 errors["Multiples contenedores"].append(medi_own_key2)
#                 continue
#             except Exception as e:
#                 errors["Otros errores"].append(medi_own_key2)
#                 print("e", e)
#                 continue
#
#         else:
#             errors["No tiene formato correcto"].append(medicament.own_key2)
#     return success_count, errors
#
#
# def reporte_med_container():
#     successes_medicament, errors_medicament = update_med_container_id()
#     print("Casos exitosos:", successes_medicament)
#     error_count = 0
#     for key, values in errors_medicament.items():
#         error_count += len(values)
#         print(key, len(values))
#     print("Conteo total de errores:", error_count)
#
#     print(errors_medicament["Key no encontrada"][:20])
#
#
# # reporte_med_container()
#
#
# Elimina los ultimos caracteres e intenta buscar los contenedores sin
# revisar cuales caracteres son.
# def update_med_container_id():
#     from med_cat.models import Medicament
#     from medicine.models import Container
#     from geo.models import Provider
#     entity_imss = Provider.objects.get(id=55)
#     medicaments_own_imss = Medicament.objects.filter(
#         entity=entity_imss)
#     errors = {
#         "Key no encontrada": [], "No tiene formato correcto": [],
#         "Multiples contenedores": [], "Otros errores": []}
#     success_count = 0
#
#     for medicament in medicaments_own_imss:
#         # Llave sin los 00 insertados en la posición [10] y [11]
#         # medi_own_key2 = medicament.own_key2[:-4] + medicament.own_key2[-2:]
#         # Complemento de medi_own_key2, es decir, los caracteres extra
#         # agregados, '00'
#         # comp_medi_own_key2 = medicament.own_key2[-4:-2]
#         medi_own_key2 = medicament.own_key2[:-2]
#         # if comp_medi_own_key2 == '00':
#         try:
#             container_found = Container.objects.get(key2=medi_own_key2)
#             success_count += 1
#             medicament.container = container_found
#             # medicament.save()
#         except Container.DoesNotExist:
#             errors["Key no encontrada"].append(medicament.own_key2)
#         except Container.MultipleObjectsReturned:
#             errors["Multiples contenedores"].append(medicament.own_key2)
#         except Exception as e:
#             errors["Otros errores"].append(medicament.own_key2)
#             print("e", e)
#
#     return success_count, errors
#
#
# def reporte_med_container():
#     successes_medicament, errors_medicament = update_med_container_id()
#     print("Casos exitosos:", successes_medicament)
#     error_count = 0
#     for key, values in errors_medicament.items():
#         error_count += len(values)
#         print(key, len(values))
#     print("Conteo total de errores:", error_count)
#
#     print(errors_medicament["Multiples contenedores"])
#
#
# reporte_med_container()
#
#
# def update_med_container_id():
#     from med_cat.models import Medicament
#     from medicine.models import Container
#     from geo.models import Provider
#     entity_imss = Provider.objects.get(id=55)
#     medicaments_own_imss = Medicament.objects.filter(
#         entity=entity_imss)
#     errors = {
#             "Key no encontrada": [], "Multiples contenedores": [],
#             "Otros errores": []}
#     success_count = 0
#     success_count_bad_format = 0
#
#     for medicament in medicaments_own_imss:
#         # Llave sin los 00 insertados en la posición [10] y [11]
#         medi_own_key2 = medicament.own_key2[:-4] + medicament.own_key2[-2:]
#         # Complemento de medi_own_key2, es decir, los caracteres extra
#         # agregados, '00'
#         comp_medi_own_key2 = medicament.own_key2[-4:-2]
#         if comp_medi_own_key2 == '00':
#             container_found = Container.objects \
#                 .filter(key2=medi_own_key2).first()
#             if container_found:
#                 success_count += 1
#                 medicament.container = container_found
#                 # medicament.save()
#             else:
#                 errors["Key no encontrada"].append(medi_own_key2)
#             try:
#                 # container_found = Container.objects.get(key2=medi_own_key2)
#                 # success_count += 1
#                 # medicament.container = container_found
#                 # medicament.save()
#             except Container.DoesNotExist:
#                 errors["Key no encontrada"].append(medi_own_key2)
#                 continue
#             except Container.MultipleObjectsReturned:
#                 errors["Multiples contenedores"].append(medi_own_key2)
#                 continue
#             # Checar códigos 030, 040, 020
#             except Exception as e:
#                 errors["Otros errores"].append(medi_own_key2)
#                 print("e", e)
#                 continue
#
#         else:
#             medi_own_key2_lastd = medicament.own_key2[:-2]
#             # Otra condicional
#             try:
#                 container_found = Container.objects.get(
#                     key2=medi_own_key2_lastd)
#                 success_count_bad_format += 1
#                 medicament.container = container_found
#             except Container.DoesNotExist:
#                 errors["Key no encontrada"].append(medi_own_key2_lastd)
#                 continue
#             except Container.MultipleObjectsReturned:
#                 errors["Multiples contenedores"].append(medi_own_key2_lastd)
#                 continue
#             except Exception as e:
#                 errors["Otros errores"].append(medi_own_key2_lastd)
#                 print("e", e)
#                 continue
#         print("All good.")
#
#     return success_count, success_count_bad_format, errors
#
#
# def reporte_med_container():
#     successes_medicament, successes_bad_format, errors_medicament = (
#         update_med_container_id())
#     print("Casos exitosos", successes_medicament)
#     print("Casos exitosos con mal formato ('00' al final)",
#           successes_bad_format)
#     error_count = 0
#     for key, values in errors_medicament.items():
#         error_count += len(values)
#         print(key, len(values))
#     print("Conteo total de errores", error_count)
#
#
# reporte_med_container()


# Elimina los ultimos caracteres e intenta buscar los contenedores sin
# revisar cuales caracteres son. Además, intenta filtrar duplicados
def update_med_container_id():
    from med_cat.models import Medicament
    from medicine.models import Container
    from geo.models import Provider
    entity_imss = Provider.objects.get(id=55)
    medicaments_own_imss = Medicament.objects.filter(
        entity=entity_imss)
    errors = {
        "Key no encontrada": [], "No tiene formato correcto": [],
        "Multiples contenedores": [], "Otros errores": []}
    success_count = 0
    for medicament in medicaments_own_imss:
        medi_own_key2 = medicament.own_key2[:-2]
        container_found = Container.objects\
            .filter(key2=medi_own_key2).first()
        if container_found:
            success_count += 1
            medicament.container = container_found
            # medicament.save()
        else:
            errors["Key no encontrada"].append(medicament.own_key2)
    return success_count, errors


def reporte_med_container():
    successes_medicament, errors_medicament = update_med_container_id()
    print("Casos exitosos:", successes_medicament)
    error_count = 0
    for key, values in errors_medicament.items():
        error_count += len(values)
        print(key, len(values))
    print("Conteo total de errores:", error_count)


# reporte_med_container()


