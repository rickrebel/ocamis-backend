# -*- coding: utf-8 -*-
from desabasto.medicines import all_rows
from desabasto.models import (
    Component, Container, Group, Presentation, PresentationType)
from pprint import pprint
import re
import json

"""
excepciones:
    # En el mismo renglón hay varias claves
    # Hay más de una presentación en el mismo grupo.

Limpiezas previas:
    # Eliminar las filas vacías
"""


# format_key = re.compile(r'^0\d0\.000\.\d{4}\.\d{2}$')
format_key = re.compile(r'0\d0\.000\.\d{4}\.\d{2}')
format_header = re.compile(r'^Clave')
# Excepciones que no están completamente en mayúsculas:
format_present = re.compile(
    '^(Granulado Oral|Tableta|Comprimido|Cápsula|POLVO|CÁPSULA).*')


def to_work(selected_rows=None, exp=True):
    components = []
    idx_subt = -5
    current_group = None
    current_comp = None
    for idx, row in enumerate(selected_rows or all_rows):
        # print( row)
        """if row[0] == u'Clave':
            if not selected_rows[idx-1][0]:
                print( selected_rows[idx-1])
                print( selected_rows[idx-2])"""
        # Descartamos cuando diga 'Cuadro Básico o cuando estén vacías las
        # filas'
        if (
            not row[0] or re.match('^(Cuadro|Catálogo)', row[0])
        ) and not row[1]:
            continue
        # Cuando sea el encabezado
        if format_header.match(row[0]):
            continue
        # Es el nombre de un grupo
        if re.match(r'^Grupo', row[0]):
            sepp = row[0].index(':')
            if exp:
                current_group = int(row[0][sepp - 2: sepp])
            else:
                current_group, is_created = Group.objects.get_or_create(
                    number=int(row[0][sepp - 2: sepp]),
                    name=row[0][sepp + 1:])
            continue
        # Si se trata del comienzo de un componente
        try:
            next_row = all_rows[idx + 1]
            if re.match(r'Clave', next_row[0]):
                # print( row[0])
                if exp:
                    components.append({
                        "name": row[0],
                        "group": current_group,
                        "presentations_raw": [],
                    })
                else:
                    current_comp, is_created = Component.objects\
                        .get_or_create(
                            name=row[0],
                            group=current_group,
                            presentations_raw='[]')
                current_presents = []
                continue
        except Exception as e:
            print(e)
            print(u"Llegamos al final")
        if exp:
            if len(components):
                current_comp = components[-1]
        # Nombres de las presentaciones
        # Los identificaremos porque están en mayúsculas, es decir, no tiene
        # minúsculas y tiene una longitud de al menos 5 caracteres
        has_minusc = not re.match(r'.*[a-z].*', row[1])
        some_alterative = format_present.match(row[1])
        has_chars = len(re.findall(r'\w', row[1])) > 2
        sample_numbers = not len(re.findall(r'\d{3}', row[1]))
        if (has_minusc or some_alterative) and has_chars and sample_numbers:
            if idx_subt + 1 == idx:
                current_presents[-1]["name"] += u" %s" % row[1]
            else:
                current_presents.append({
                    'name': row[1],
                    'texts': [],
                    'keys': []
                })
            idx_subt = idx
        # Si no, entonces sabemos que es parte del texto
        else:
            # Se limpian los dobles espacios
            curr_text = re.sub(r' +', ' ', row[1])
            current_presents[-1]['texts'].append(curr_text)
        # Cuando la primera columna tiene una clave de medicamento:
        for key in re.findall(format_key, row[0]):
            current_presents[-1]['keys'].append({"key": key})
        if exp:
            current_comp["presentations_raw"] = current_presents
            components[-1] = current_comp
        else:
            current_comp.presentations_raw = json.dumps(current_presents)
            current_comp.save()
    print(len(components))
    return components


def to_work2(selected_rows=None, exp=True, final_comps=[]):
    base_comps = final_comps if exp else Component.objects.all()
    for comp in base_comps:
        try:
            base_presents = comp["presentations_raw"] if exp else json.loads(
                comp.presentations_raw)
        except TypeError:
            base_presents = []
        final_presents = []
        for present in base_presents:

            {
                "keys": [
                    {
                        "key": "020.000.0153.00"
                    }
                ],
                "texts": [
                    "Cada frasco ámpula contiene:",
                    "No menos de 1 000 DICC50 (3,0 log10 DICC50) de virus "
                    "de la rubeola de cepa RA27/3 y no más de 25 µg de "
                    "sulfato de neomicina B.",
                    "Envase con frasco ámpula",
                    "con 0.5 ml."
                ],
                "name": "SOLUCION INYECTABLE"
            }

            curr_jumps = 0
            # start_prev = 0
            any_envase = False
            real_idx_start = 0
            potencial_env_uniq = ''
            potential_desc = ''
            for idx, key in enumerate(present["keys"]):
                texts = present["texts"]
                curr_envase = False
                prev_envase = False
                try:
                    potencial_env = texts[-idx - 1 - curr_jumps]
                    curr_envase = u'nvase' in texts[-idx - 1 - curr_jumps]
                    is_conector = potencial_env == 'o' or potencial_env == 'ó'
                    if is_conector:
                        curr_jumps += 1
                        potencial_env = texts[-idx - 1 - curr_jumps]
                except Exception as e:
                    print(e)
                    if exp:
                        pprint(comp["name"])
                    else:
                        pprint(comp.name)
                    pprint(present)
                if not curr_envase:
                    try:
                        prev_envase = u'nvase' in texts[-idx - 2 - curr_jumps]
                        if prev_envase:
                            potencial_env = "%s %s" % (
                                texts[-idx - 2 - curr_jumps],
                                texts[-idx - 1 - curr_jumps]
                            )
                            curr_jumps += 1
                    except Exception as e:
                        print(e)
                        # a = 1
                    if len(present["keys"]) == 1 and not prev_envase:
                        for txt in texts:
                            if u'nvase' in txt:
                                any_envase = True
                                potencial_env_uniq = txt
                            elif any_envase:
                                potencial_env_uniq += " %s" % txt
                            else:
                                potential_desc += " %s" % txt
                        if any_envase:
                            key["container"] = potencial_env_uniq
                            continue
                if curr_envase or prev_envase:
                    real_idx_start = -idx - 1 - curr_jumps
                key["container"] = potencial_env
            if not potential_desc and real_idx_start < 0:
                for txt in texts[:real_idx_start]:
                    potential_desc += " %s" % txt

            present["description"] = potential_desc
            if not exp:
                final_presents.append(present)

        if not exp:
            comp.presentations_raw = json.dumps(final_presents)
            comp.save()


# SOLO PARA BASE DE DATOS


def to_work3(selected_rows=None):
    for comp in Component.objects.all():
        try:
            presents = json.loads(comp.presentations_raw)
        except TypeError:
            presents = []
        for present in presents:
            pres_type, is_created = PresentationType.objects.get_or_create(
                name=present["name"])
            present_obj = Presentation.objects.create()
            for key in present["keys"]:
                # A continuación, quitar el previo 'Envase con ' para el
                # short_name
                short_name = key["container"]
                Container.objects.create()


def run_importation(exp=True, save_json=False):
    # Se trata de experimentación previa?

    final_comps = to_work(all_rows, exp=exp)

    to_work2(exp=exp, final_comps=final_comps)
    to_work3()

    """
    with open('medicamentos.json', 'w') as outfile:
        json.dump(final_comps, outfile)

    # Los que no tienen exacta congruencia:
    for comp in final_comps:
        for present in comp["presentations"]:
            if not len(present["keys"]):
                pprint(comp["name"])
                pprint(comp)

    # Las que no parece que tuvieran un buen resultado de container:
    for comp in final_comps:
        for present in comp["presentations"]:
            curr_jumps = 0
            for idx, key in enumerate(present["keys"]):
                if u'nvase' not in key["container"]:
                    print( comp["name"])
                    print( key["container"])

    # Búsqueda para encontrar presentaciones que tienen más de 3 dígitos
    # seguidos.
    for comp in final_comps:
        for present in comp["presentations"]:
            if len(re.findall(r'\d{3}', present["name"])):
                print( present["name"])
                pprint(comp["name"])
                pprint(comp)
    """
