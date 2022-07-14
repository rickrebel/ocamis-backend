

import re
case_tests = [
    "UNIDAD DE MEDICINA FAMILIAR NO.",
    "UNIDAD DE MEDICINA FAMILIAR NO",
    "U MEDICA FAMILIAR",
]



re_no_point = re.compile(r'(\sNO.?)$')

for case in case_tests:
    final_name = re.sub(re_no_point, '', case)
    print(final_name)
    #splited = final_name.split("|")

 
re_consul = re.compile(r'( CONSULTA MEDICINA FAMILIAR)')

for case in case_tests:
    print(case)
    final_name = re.sub(re_consul, '|CONSULTA MEDICINA FAMILIAR', case)
    #final_name = re.sub(re_consul, '\\1|CONSULTA MEDICINA FAMILIAR - \\2', case)
    print(final_name)
    #splited = final_name.split("|")

 