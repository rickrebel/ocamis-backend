from medicine.models import Presentation, Component
from report.models import Supply
import re


all_pres = Presentation.objects.filter(
    description__isnull=False, 
    component__is_vaccine=False,
    component__frequency__gt=0)


valids = {
    u'mg': True, 
    u'g': True, 
    u'ml': True, 
    u'UI': True, 
    u'cm2': True, 
    u'U': True, 
    u'mEq': True, 
    u'µg': True, 
    u'mL': True
}


count_print = 0
all_types = {}
for pres in all_pres:
    desc = pres.description
    try:
        after_point = desc[desc.index(": ") + 1:]
    except Exception as e:
        continue
    iters = re.finditer(r"\d\s([a-zA-Z]+)[\.|\s|^]", after_point)
    curr_pres = False
    iters_count = 0
    for curr_iter in iters:
        iters_count+=1
        measure = after_point[curr_iter.start(1):curr_iter.end(1)]
        if measure not in all_types:
            all_types[measure] = 1
            if not measure in valids:
                if len(after_point) > 250:
                    if pres.presentation_type.name != u'POLVO O SUSPENSIÓN ORAL':
                        print(">>>> ", pres.presentation_type)
                else:
                    curr_pres = True
                    print("____ %s _________" % measure)
                    print(after_point)
        else:
            all_types[measure] += 1
    if iters_count > 1 and len(after_point) < 250:
        print("---------VARIOS-------------")
        print(after_point)
    if curr_pres:
        count_print += 1
    if count_print > 100:
        print(count_print)
        break







print(all_types)
for type_pres in all_types.iteritems():
    print(type_pres)

algo = u"Benzatina bencilpenicilina equivalente a 600 000 UI de bencilpenicilina."
end_digit = re.search(r"\s(\w+)[\.|\s|^]", algo)
print(end_digit.start())



all_comps = Component.objects.all()
for comp in all_comps:
    comp.frequency = Supply.objects\
        .filter(component=comp).distinct().count()
    print(comp.frequency)
    comp.save()