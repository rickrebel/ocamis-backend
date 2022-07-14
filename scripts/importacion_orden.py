# -*- coding: utf-8 -*-
from desabasto.models import (PurchaseRaw)
# import csv
import io
import re

f = open('ordenes.txt', 'r')

all_text = f.read()
print(all_text)


# def insert_purchases():
file = 'ordenes.txt'
with io.open(file, "r", encoding='utf-8') as File:
    # total_rows = File.readlines()
    # total_rows = File.read().decode('latin-1').encode("utf-8")
    total_rows = File.read()
    all_lines = total_rows.split("\n")
    len(all_lines)
    # reader = csv.reader(File)
    x = 0
    prev_cut = 0
    current_doc = u""
    # for row in reader:
    for row in all_lines:
        # data = row[0].decode('latin-1').encode("utf-8")
        # data = row.decode('latin-1').encode("utf-8")
        data = row
        # print( data)
        # print( type(data))
        if data == u'Documento sin validez oficial':
            prev_cut += 1
        else:
            prev_cut = 0
            current_doc = u"%s\n%s" % (current_doc, data)
            # current_doc = data
        if prev_cut == 1:
            # print( current_doc)
            PurchaseRaw.objects.create(raw_pdf=current_doc)
            current_doc = u''
        elif prev_cut > 1:
            continue
        x += 1
    print(x)


same_line = [
    {"text": u'RFC', "field": 'rfc'},
    {"text": u'Razón Social', "field": 'proveedor'},
    {"text": u'Fecha expedición de la orden', "field": 'expedition_date'},
    {"text": u'Fecha límite de entrega de la orden', "field": 'deliver_date'},
    {"text": u'Almacén entrega', "field": 'warehouse'},
    {"text": u'INSTITUCIÓN REQUIRENTE', "field": 'inst'},
    {
        "text": u'NÚMERO DE ORDEN DE SUMINISTRO', "field": 'orden',
        "is_next": True
    },
    {"text": u'Contrato Procedimiento', "field": 'contrato', "is_next": True},
]
re_has_cve = re.compile(r'^(\w{5})(\d{6})\s')

for purchase in PurchaseRaw.objects.all()[:1]:
    raw_lines = purchase.raw_pdf.split("\n")
    prev_simple = None
    found_text = False
    prev_complex = 0
    description_text = []
    clues_text = []
    for line in raw_lines:
        print("next_line:")
        print(line)
        print("______________")
        if line[:4] == 'ITEM':
            print("--------item")
            prev_complex = 1
            continue
        if prev_complex:
            print("--------prev_complex")
            if line == 'ORDEN DE SUMINISTRO':
                purchase.descripcion = ' '.join(description_text)
                purchase.clues = ' '.join(clues_text)
                print(u".......description y clues")
                print(' '.join(description_text))
                print(' '.join(clues_text))
                print(u"%s: %s" % ('prev_complex', prev_complex))
                prev_complex = 0
            elif (bool(re.search(re_has_cve, line))):
                prev_complex += 1
            elif prev_complex == 1:
                print("clave_insumo: %s" % line[2:])
                purchase.clave_insumo = line[2:]
                prev_complex += 1
            elif prev_complex == 2:
                description_text.append(line)
            if prev_complex == 3:
                clues_text.append(line)
            continue
        if prev_simple:
            print("--------prev_simple: %s" % prev_simple)
            setattr(purchase, prev_simple, line)
            prev_simple = None
            continue
        for same in same_line:
            len_text = len(same["text"])
            if line[:len_text] == same["text"]:
                print("--------coincide")
                if "is_next" in same:
                    prev_simple = same["field"]
                else:
                    setattr(purchase, same["field"], line[len_text+2:])
                break
    print(purchase)
    purchase.save()


PurchaseRaw.objects.all().count()

PurchaseRaw.objects.all().delete()


p = re.compile("[a-z]")
for m in p.finditer('a1b2c3d4'):
    print((m.start(), m.group()))
    print((m.start()))
